"""
Manejadores generales de comandos y callbacks para el bot de Telegram.

Este módulo contiene handlers que no son específicos de una funcionalidad
particular, como comandos básicos y el dispatcher principal de callbacks.
"""
import asyncio
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from .base.keyboards import Keyboards
from .base.messages import Messages
from .requisiciones.handlers_requisiciones import (
    handle_menu_callbacks,
    handle_requisicion_callbacks,
    handle_requisicion_messages,
)
from .requisiciones.services_requisiciones import RequisicionService
from .utils import (
    handle_errors,
    log_command,
    require_auth,
    escape_markdown,
)
from .sessions import UserSession

logger = logging.getLogger(__name__)


# ============================================================================
# COMANDOS BÁSICOS
# ============================================================================

@handle_errors
@log_command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /start - Maneja el inicio de sesión de usuarios.
    
    Si el usuario ya está registrado, muestra el menú principal con opciones según su rol.
    Si no está registrado, inicia el proceso de registro.
    """
    from .base.keyboards import Keyboards
    from .sessions import UserSession
    
    # Verificar si el usuario ya está registrado
    if UserSession.is_user_registered(context):
        # Obtener información del usuario desde la sesión
        user_data = UserSession.get_user_data(context)
        es_supervisor = user_data.get('es_supervisor', False)
        es_directivo = user_data.get('es_directivo', False)
        
        # Mostrar menú principal según el rol
        await update.message.reply_text(
            "¡Bienvenido de nuevo! ¿En qué puedo ayudarte hoy?",
            parse_mode='Markdown',
            reply_markup=await Keyboards.menu_principal(es_supervisor, es_directivo)
        )
    else:
        # Iniciar proceso de registro
        from .utils import start_registration
        await start_registration(update, context)


@handle_errors
@log_command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el menú de ayuda con el ID de Telegram del usuario.
    """
    user = update.effective_user
    chat_id = str(user.id)
    
    mensaje_ayuda = (
        "🤖 *Menú de Ayuda*\n\n"
        "📋 *Comandos disponibles:*\n"
        "• /nueva - Iniciar una nueva requisición\n"
        "• /mis_requisiciones - Ver tus requisiciones\n"
        "• /ver <ID> - Ver detalles de una requisición\n"
        "• /ayuda - Muestra este mensaje de ayuda\n\n"
        f"🆔 *Tu ID de Telegram:*\n`{chat_id}`\n\n"
        "📝 *Nota:* Comparte este ID con el administrador para vincular tu cuenta."
    )
    
    await update.message.reply_text(
        mensaje_ayuda,
        parse_mode='Markdown',
        reply_markup=Keyboards.menu_principal()
    )





# ============================================================================
# CALLBACK HANDLERS (Botones inline)
# ============================================================================

@handle_errors
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Dispatcher principal para manejar todos los callbacks de botones inline.

    Este handler delega el procesamiento a handlers específicos según el tipo
    de callback, manteniendo la separación de responsabilidades.
    """
    query = update.callback_query
    await query.answer()

    data = query.data

    # Manejar paginación
    if data.startswith('page_'):
        try:
            page = int(data.split('_')[1])
            # Obtener el mensaje original
            original_message = query.message.text
            
            # Obtener el estado del usuario para saber qué tipo de lista mostrar
            user_data = UserSession.get_user_data(context)
            
            # Importaciones necesarias
            from asgiref.sync import sync_to_async
            from Almacen.models.telegram_user import TelegramUser
            from Almacen.models.personal.personal import Empleado
            
            # Obtener el empleado actual
            try:
                telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=update.effective_user.id)
                empleado = await sync_to_async(getattr)(telegram_user, 'empleado', None)
                
                if not empleado:
                    empleado = await sync_to_async(Empleado.objects.filter(telegram_id=telegram_user.telegram_id).first)()
                
                # Obtener las requisiciones según el contexto
                if 'mis_requisiciones' in original_message.lower():
                    # Si es la lista de mis requisiciones
                    if hasattr(RequisicionService, 'listar_requisiciones_por_empleado'):
                        # Si el método ya es asíncrono, lo llamamos directamente
                        if asyncio.iscoroutinefunction(RequisicionService.listar_requisiciones_por_empleado):
                            requisiciones = await RequisicionService.listar_requisiciones_por_empleado(empleado)
                        else:
                            requisiciones = await sync_to_async(RequisicionService.listar_requisiciones_por_empleado)(empleado)
                    else:
                        # Si no existe el método, filtrar manualmente
                        if asyncio.iscoroutinefunction(RequisicionService.listar_requisiciones):
                            all_reqs = await RequisicionService.listar_requisiciones()
                        else:
                            all_reqs = await sync_to_async(RequisicionService.listar_requisiciones)()
                        requisiciones = [r for r in all_reqs if getattr(r, 'solicitante_id', None) == empleado.id]
                else:
                    # Si es otra lista (ej: todas las requisiciones)
                    if asyncio.iscoroutinefunction(RequisicionService.listar_requisiciones):
                        requisiciones = await RequisicionService.listar_requisiciones()
                    else:
                        requisiciones = await sync_to_async(RequisicionService.listar_requisiciones)()
                
                # Asegurarse de que tenemos una lista
                if not isinstance(requisiciones, list):
                    requisiciones = list(requisiciones)
                
                # Reconstruir el teclado con la página solicitada
                # Deshabilitar show_actions para que no muestre botones de aprobación/rechazo en la lista
                keyboard = Keyboards.lista_requisiciones(
                    requisiciones,
                    page=page,
                    items_per_page=5,
                    show_actions=False  # Deshabilitar acciones en la lista general
                )
                
                # Actualizar solo el teclado
                await query.edit_message_reply_markup(reply_markup=keyboard)
                await query.answer()  # Para quitar el reloj de carga
                return True
                
            except TelegramUser.DoesNotExist:
                logger.error("Usuario de Telegram no encontrado")
                await query.answer("❌ Error: Usuario no encontrado")
                return True
                
        except Exception as e:
            logger.error(f"Error en paginación: {e}", exc_info=True)
            await query.answer("❌ Error al cambiar de página. Intenta de nuevo.")
            return True
    
    # Ignorar el callback 'noop' (botón inactivo)
    if data == 'noop':
        await query.answer()
        return True
    
    # Intentar handlers específicos de menú
    if await handle_menu_callbacks(update, context, data):
        return

    # Intentar handlers específicos de requisiciones
    if await handle_requisicion_callbacks(update, context, data):
        return

    # Callbacks generales
    if data == "menu_principal":
        # Get user role information
        user_data = UserSession.get_user_data(context)
        es_supervisor = user_data.get('es_supervisor', False)
        es_directivo = user_data.get('es_directivo', False)
        
        try:
            # Try to edit the existing message
            await query.edit_message_text(
                Messages.WELCOME,
                parse_mode=None,
                reply_markup=await Keyboards.menu_principal(
                    es_supervisor=es_supervisor,
                    es_directivo=es_directivo
                )
            )
        except Exception as e:
            # If editing fails (e.g., message is a photo), send a new message
            await query.message.reply_text(
                Messages.WELCOME,
                parse_mode=None,
                reply_markup=await Keyboards.menu_principal(
                    es_supervisor=es_supervisor,
                    es_directivo=es_directivo
                )
            )
            # Delete the callback query message if possible
            try:
                await query.message.delete()
            except:
                pass

    elif data == "help":
        help_message = await Messages.get_help_message(update)
        await query.edit_message_text(
            help_message,
            parse_mode='Markdown',
            reply_markup=Keyboards.ayuda()
        )

    elif data == "cancel":
        UserSession.clear_user_state(context)
        UserSession.clear_temp_requisicion(context)

        await query.edit_message_text(
            "❌ Operación cancelada.",
            parse_mode='Markdown'
        )
        
    elif data == "limpiar_y_menu":
        # Obtener información del usuario
        user_data = UserSession.get_user_data(context)
        es_supervisor = user_data.get('es_supervisor', False)
        es_directivo = user_data.get('es_directivo', False)
        
        # Obtener el menú principal
        menu_markup = await Keyboards.menu_principal(
            es_supervisor=es_supervisor,
            es_directivo=es_directivo
        )
        
        try:
            # Intentar eliminar el mensaje anterior
            await query.message.delete()
        except Exception as e:
            logger.warning(f"No se pudo eliminar el mensaje: {e}")
        
        # Enviar un nuevo mensaje con el menú principal
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=Messages.WELCOME,
            parse_mode='Markdown',
            reply_markup=menu_markup
        )

    else:
        logger.warning(f"Callback no manejado: {data}")
        await query.edit_message_text(
            "❌ Acción no reconocida.",
            parse_mode='Markdown'
        )


# ============================================================================
# MESSAGE HANDLER (Conversaciones)
# ============================================================================

@handle_errors
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Dispatcher principal para manejar mensajes de texto en conversaciones.

    Delegamos a handlers específicos según el estado de la conversación.
    """
    state = UserSession.get_user_state(context)
    text = update.message.text

    # Manejar registro de usuario
    if state == 'esperando_nombre_registro':
        from .utils import complete_registration
        await complete_registration(update, context, text)
        return

    # Intentar handlers específicos de requisiciones
    if await handle_requisicion_messages(update, context, state, text):
        return

    # Mensaje sin contexto específico
    await update.message.reply_text(
        "No entiendo ese mensaje. Usa /help para ver los comandos disponibles.",
        reply_markup=Keyboards.menu_principal()
    )


# ============================================================================
# PHOTO HANDLER (Para imágenes en requisiciones)
# ============================================================================

@handle_errors
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la recepción de fotos para requisiciones.

    Args:
        update: Update de Telegram con foto
        context: Contexto de la conversación
    """
    state = UserSession.get_user_state(context)
    logger.info(f"Foto recibida. Estado actual: {state}")

    if state == 'esperando_imagen':
        logger.info("Procesando imagen para requisición")
        await handle_imagen_requisicion(update, context)
    else:
        logger.warning(f"Foto recibida pero no se esperaba. Estado: {state}")
        # Get the user data to determine the menu options
        user_data = UserSession.get_user_data(context)
        es_supervisor = user_data.get('es_supervisor', False)
        es_directivo = user_data.get('es_directivo', False)
        
        # Get the menu principal keyboard
        keyboard = await Keyboards.menu_principal(
            es_supervisor=es_supervisor,
            es_directivo=es_directivo
        )
        
        await update.message.reply_text(
            "No estoy esperando una imagen en este momento.\n\n"
            "Para crear una requisición, usa el comando /nueva",
            reply_markup=keyboard
        )


async def handle_imagen_requisicion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la subida de imagen para una requisición.

    Args:
        update: Update de Telegram con foto
        context: Contexto de la conversación
    """
    try:
        # Informar que se está procesando
        await update.message.reply_text(
            "📷 Procesando imagen, por favor espera...",
            parse_mode='Markdown'
        )
        
        # Obtener la foto de mayor resolución
        photo = update.message.photo[-1]  # Última es la de mayor calidad

        # Descargar la imagen
        file = await context.bot.get_file(photo.file_id)
        image_data = await file.download_as_bytearray()

        # Convertir a BytesIO para Django
        from io import BytesIO
        from PIL import Image
        import os

        image_buffer = BytesIO(image_data)
        image = Image.open(image_buffer)

        # Generar nombre único para la imagen
        import uuid
        filename = f"requisicion_{uuid.uuid4().hex[:8]}.jpg"

        # Guardar imagen en el directorio media/requisiciones/
        from django.conf import settings
        media_dir = os.path.join(settings.MEDIA_ROOT, 'requisiciones')
        os.makedirs(media_dir, exist_ok=True)

        # Guardar la imagen
        filepath = os.path.join(media_dir, filename)
        try:
            # Asegurarse de que la imagen esté en modo RGB (evita errores con PNG/JPEG)
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            image.save(filepath, 'JPEG', quality=85)
            logger.info(f"Imagen guardada en: {filepath}")
            
            # Obtener la ruta relativa para guardar en el modelo
            relative_path = os.path.join('requisiciones', filename)
            
            # Obtener la requisición temporal
            temp_req = UserSession.get_temp_requisicion(context)
            if not temp_req:
                raise ValueError("No se encontró información de la requisición en la sesión")

            # Guardar la ruta relativa de la imagen en los datos temporales
            temp_req['imagen'] = relative_path
        except Exception as e:
            logger.error(f"Error al guardar la imagen: {e}")
            raise
        UserSession.set_temp_requisicion(context, temp_req)

        # Crear la requisición con todos los datos recopilados y la imagen
        telegram_user = await UserSession.get_telegram_user(update)

        requisicion = await RequisicionService.crear_requisicion(
            obra=temp_req.get('obra'),
            ubicacion=temp_req.get('ubicacion'),
            especialidad=temp_req.get('especialidad'),
            supervisor_id=temp_req.get('supervisor'),  # ID del supervisor seleccionado
            fecha_util=temp_req.get('fecha_util'),
            solicitante_nombre=temp_req.get('solicitante_nombre'),
            bloque_id=temp_req.get('bloque_id'),
            telegram_user=telegram_user,
            imagen=temp_req.get('imagen')
        )

        # Generate Dreacht Hub link for completing the requisition
        from django.conf import settings
        dreacht_hub_url = getattr(settings, 'DREACHT_HUB_URL', 'http://localhost:8001')
        completion_link = f"{dreacht_hub_url}/requisiciones/edit/{requisicion.token_publico}/"
        
        mensaje = (
            f"✅ *Requisición Creada Exitosamente*\n\n"
            f"*ID:* `{requisicion.id}`\n"
            f"*Solicitante:* {escape_markdown(temp_req.get('solicitante_nombre', 'N/A'))}\n"
            f"*Ubicación:* {escape_markdown(requisicion.ubicacion)}\n"
            f"*Obra:* {escape_markdown(requisicion.obra)}\n"
            f"*Supervisor:* {escape_markdown(temp_req.get('supervisor_nombre', 'N/A'))}\n"
            f"*Fecha utilización:* {temp_req.get('fecha_util', 'N/A')}\n"
            f"*Especialidad:* {escape_markdown(requisicion.especialidad)}\n"
            f"*Estado:* Pendiente\n\n"
            f"🔗 *Completa tu requisición aquí:*\n"
            f"{completion_link}\n\n"
            f"👆 Haz clic en el enlace para:\n"
            f"• Agregar productos\n"
            f"• Generar el PDF\n"
            f"• Finalizar la requisición"
        )

        # Crear teclado con botón de menú principal y enlace de completar
        from .base.keyboards import Keyboards
        keyboard = [
            [
                InlineKeyboardButton("🔗 Completar Requisición", url=completion_link)
            ],
            [
                InlineKeyboardButton("🏠 Menú Principal", callback_data="limpiar_y_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Enviar mensaje con el teclado
        await update.message.reply_text(
            mensaje,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

        # Limpiar estado
        UserSession.clear_user_state(context)
        UserSession.clear_temp_requisicion(context)

    except Exception as e:
        logger.error(f"Error al procesar imagen: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ *Error al procesar la imagen*\n\n"
            f"Detalle: {escape_markdown(str(e))}\n\n"
            f"Por favor, intenta nuevamente con /nueva",
            parse_mode='Markdown'
        )
        # Limpiar estado en caso de error
        UserSession.clear_user_state(context)
        UserSession.clear_temp_requisicion(context)
