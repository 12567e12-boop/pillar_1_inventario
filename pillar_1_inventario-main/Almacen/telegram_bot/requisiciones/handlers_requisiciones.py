"""
Handlers específicos para la gestión de requisiciones en el bot de Telegram.

Este módulo contiene todos los handlers relacionados con el flujo
de creación, consulta y gestión de requisiciones.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async

from ..base.messages import Messages
from ..base.keyboards import Keyboards
from .services_requisiciones import RequisicionService, CatalogoService
from ..utils import (
    handle_errors,
    log_command,
    require_auth,
    require_supervisor,
    require_directivo,
    parse_command_args,
    escape_markdown,
)
from ..sessions import UserSession
from Almacen.models.personal.personal import Empleado
from Almacen.models.requisiciones.requisiciones import Requisicion
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


logger = logging.getLogger(__name__)


# ============================================================================
# COMANDOS DE REQUISICIONES
# ============================================================================

@handle_errors
@log_command
@require_auth
async def nueva_requisicion_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /nueva - Inicia el proceso de crear una requisición.

    Inicia el flujo conversacional para crear una nueva requisición,
    comenzando por la selección del bloque.
    """
    # Responder al callback si es necesario
    if update.callback_query:
        await update.callback_query.answer()

    # Verificar que tengamos un chat válido
    if not update.effective_chat:
        logger.error("No se pudo obtener el chat efectivo para nueva_requisicion_command")
        return

    # Iniciar el flujo de creación
    UserSession.set_user_state(context, 'esperando_solicitante')
    UserSession.set_temp_requisicion(context, {})

    await update.effective_chat.send_message(
        "*Paso 1:* Ingresa el nombre del solicitante:",
        parse_mode='Markdown',
        reply_markup=Keyboards.cancelar()
    )


@handle_errors
@log_command
@require_auth
async def mis_requisiciones_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /mis_requisiciones - Lista todas las requisiciones.
    Muestra todas las requisiciones registradas, sin filtrar por usuario ni rol.
    """
    from datetime import datetime

    try:
        # Obtener todas las requisiciones sin filtrar por usuario ni estado
        requisiciones = await RequisicionService.listar_requisiciones()

        # Asegurarse de que tenemos una lista
        if not isinstance(requisiciones, list):
            requisiciones = list(requisiciones)

        # Ordenar por fecha de solicitud descendente
        requisiciones.sort(
            key=lambda x: x.fecha_soli if x.fecha_soli else datetime.min,
            reverse=True
        )

        if not requisiciones:
            await update.effective_chat.send_message(
                "📭 No hay requisiciones registradas en el sistema.",
                parse_mode='Markdown'
            )
            return

        mensaje = "📋 *Listado de Requisiciones*\n\n"
        mensaje += f"• Total: {len(requisiciones)} requisiciones\n\n"

        await update.effective_chat.send_message(
            mensaje,
            parse_mode='Markdown',
            reply_markup=Keyboards.lista_requisiciones(
                requisiciones[:10],  # Mostrar las 10 más recientes
                page=1,
                items_per_page=5,
                show_actions=False  # Sin botones de acción
            )
        )

    except Exception as e:
        logger.error(f"Error al listar requisiciones: {str(e)}", exc_info=True)
        await update.effective_chat.send_message(
            "❌ Ocurrió un error. Por favor, inténtalo de nuevo más tarde.",
            parse_mode='Markdown'
        )


@handle_errors
@log_command
@require_auth
async def ver_requisicion_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /ver <ID> - Muestra detalles de una requisición específica.

    Args:
        <ID>: ID de la requisición a consultar

    Si no se proporciona ID o no existe, informa al usuario.
    """
    args = parse_command_args(update.message.text)

    if not args:
        await update.message.reply_text(
            "❌ Debes proporcionar el ID de la requisición.\n\n"
            "Ejemplo: `/ver REQ-001-2024`",
            parse_mode='Markdown'
        )
        return

    req_id = args[0]
    requisicion = RequisicionService.obtener_requisicion(req_id)

    if not requisicion:
        await update.message.reply_text(
            Messages.REQUISICION_NO_ENCONTRADA.format(id=req_id),
            parse_mode='Markdown'
        )
        return

    mensaje = Messages.formato_requisicion(requisicion)

    # TODO: Determinar permisos del usuario basados en roles reales
    # Por ahora, asumir permisos para demo
    es_supervisor = True
    es_directivo = True

    await update.message.reply_text(
        mensaje,
        parse_mode='Markdown',
        reply_markup=Keyboards.acciones_requisicion(
            req_id,
            requisicion.estado,
            es_supervisor,
            es_directivo
        )
    )


@handle_errors
@log_command
@require_supervisor
async def aprobar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /aprobar <ID> - Aprueba una requisición como supervisor.

    Args:
        <ID>: ID de la requisición a aprobar

    Solicita confirmación antes de aprobar.
    """
    args = parse_command_args(update.message.text)

    if not args:
        await update.message.reply_text(
            "❌ Debes proporcionar el ID de la requisición.\n\n"
            "Ejemplo: `/aprobar REQ-001-2024`",
            parse_mode='Markdown'
        )
        return

    req_id = args[0]
    requisicion = RequisicionService.obtener_requisicion(req_id)

    if not requisicion:
        await update.message.reply_text(
            Messages.REQUISICION_NO_ENCONTRADA.format(id=req_id),
            parse_mode='Markdown'
        )
        return

    # Mostrar confirmación
    mensaje = Messages.CONFIRMAR_APROBACION.format(
        id=req_id,
        obra=escape_markdown(requisicion.obra),
        solicitante=escape_markdown(requisicion.solicitante.nombre if requisicion.solicitante else "N/A"),
        num_articulos=requisicion.numero_de_articulos
    )

    await update.message.reply_text(
        mensaje,
        parse_mode='Markdown',
        reply_markup=Keyboards.confirmar_accion('aprobar', req_id)
    )


@handle_errors
@log_command
@require_supervisor
async def rechazar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /rechazar <ID> - Rechaza una requisición.

    Args:
        <ID>: ID de la requisición a rechazar

    Solicita el motivo del rechazo.
    """
    args = parse_command_args(update.message.text)

    if not args:
        await update.message.reply_text(
            "❌ Debes proporcionar el ID de la requisición.\n\n"
            "Ejemplo: `/rechazar REQ-001-2024`",
            parse_mode='Markdown'
        )
        return

    req_id = args[0]
    requisicion = RequisicionService.obtener_requisicion(req_id)

    if not requisicion:
        await update.message.reply_text(
            Messages.REQUISICION_NO_ENCONTRADA.format(id=req_id),
            parse_mode='Markdown'
        )
        return

    # Solicitar motivo del rechazo
    UserSession.set_user_state(context, f'rechazando_{req_id}')

    mensaje = Messages.CONFIRMAR_RECHAZO.format(
        id=req_id,
        obra=escape_markdown(requisicion.obra)
    )

    await update.message.reply_text(
        mensaje,
        parse_mode='Markdown',
        reply_markup=Keyboards.cancelar()
    )


# ============================================================================
# HANDLERS DE CALLBACKS PARA REQUISICIONES
# ============================================================================

async def handle_menu_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> bool:
    """
    Maneja callbacks del menú principal relacionados con requisiciones.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        data: Datos del callback

    Returns:
        bool: True si el callback fue manejado, False en caso contrario
    """
    query = update.callback_query

    # Nueva requisición
    if data == "nueva_req":
        await nueva_requisicion_command(update, context)
        return True

    # Seleccionar supervisor
    elif data.startswith("supervisor_"):
        supervisor = data.replace("supervisor_", "")
        await seleccionar_supervisor_callback(update, context, supervisor)
        return True

    # Mis requisiciones
    elif data == "mis_req":
        # Marcar que estamos en el contexto de "Mis Requisiciones"
        context.user_data['from_mis_requisiciones'] = True
        await mis_requisiciones_command(update, context)
        return True
        
    # Aprobaciones pendientes para supervisores/directivos
    elif data == "pendientes_aprobacion":
        # Asegurarse de que no estamos en el contexto de "Mis Requisiciones"
        context.user_data['from_mis_requisiciones'] = False
        
        # Obtener el usuario y sus permisos
        telegram_user = await UserSession.get_telegram_user(update)
        empleado = await sync_to_async(getattr)(telegram_user, 'empleado', None)
        
        if not empleado:
            empleado = await sync_to_async(Empleado.objects.filter(telegram_id=telegram_user.telegram_id).first)()
        
        # Si es directivo, mostrar aprobaciones pendientes de directivo
        if empleado and empleado.rol == 'directivo':
            await listar_pendientes_directivo(update, context)
        # Si es supervisor, mostrar aprobaciones pendientes de supervisor
        elif empleado and empleado.rol == 'supervisor':
            await mis_requisiciones_command(update, context)
        else:
            await update.callback_query.answer("No tienes permisos para ver aprobaciones pendientes.", show_alert=True)
        return True

    return False


async def listar_pendientes_directivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra las requisiciones pendientes de aprobación por directivo.
    """
    from asgiref.sync import sync_to_async
    
    try:
        query = update.callback_query
        await query.answer()
        
        # Obtener el usuario
        telegram_user = await UserSession.get_telegram_user(update)
        
        # Obtener empleado asociado
        empleado = await sync_to_async(getattr)(telegram_user, 'empleado', None)
        if not empleado:
            empleado = await sync_to_async(Empleado.objects.filter(telegram_id=telegram_user.telegram_id).first)()
        
        if not empleado or empleado.rol != 'directivo':
            await query.edit_message_text(
                "❌ No tienes permisos de directivo para ver esta información.",
                reply_markup=Keyboards.volver_menu_principal()
            )
            return
            
        # Obtener requisiciones pendientes de aprobación de directivo (estado 'supervisor')
        requisiciones = await RequisicionService.listar_requisiciones(
            estado='supervisor',
            excluir_estados=['rechazada', 'cerrada']
        )
        
        if not requisiciones:
            await query.edit_message_text(
                "✅ No hay requisiciones pendientes de aprobación por directivo en este momento.",
                reply_markup=Keyboards.volver_menu_principal()
            )
            return
            
        # Mostrar la lista de requisiciones
        mensaje = "📋 *Requisiciones Pendientes de Aprobación (Directivo):*\n\n"
        
        for i, req in enumerate(requisiciones[:10], 1):  # Mostrar máximo 10
            mensaje += (
                f"{i}. `{req.id}` - {req.obra}\n"
                f"   Solicitante: {req.solicitante.nombre if req.solicitante else 'N/A'}\n"
                f"   Fecha: {req.fecha_soli}\n"
                f"   Aprobada por supervisor: {'✅' if req.autorizado_supervisor else '❌'}\n\n"
            )
        
        if len(requisiciones) > 10:
            mensaje += f"\nY {len(requisiciones) - 10} más..."
            
        # Crear teclado con las primeras 5-10 requisiciones
        keyboard = []
        for req in requisiciones[:5]:  # Máximo 5 botones
            keyboard.append([
                InlineKeyboardButton(
                    f"📋 {req.id} - {req.obra[:20]}{'...' if len(req.obra) > 20 else ''}",
                    callback_data=f"ver_req_{req.id}"
                )
            ])
            
        keyboard.append([
            InlineKeyboardButton("🔄 Actualizar", callback_data="pendientes_aprobacion"),
            InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_principal")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Editar el mensaje con la lista de requisiciones
        await query.edit_message_text(
            mensaje,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
            
    except Exception as e:
        logger.error(f"Error en listar_pendientes_directivo: {e}")
        error_msg = "❌ Ocurrió un error al cargar las requisiciones pendientes."
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await update.message.reply_text(error_msg)


async def handle_requisicion_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> bool:
    """
    Maneja callbacks específicos de requisiciones.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        data: Datos del callback

    Returns:
        bool: True si el callback fue manejado, False en caso contrario
    """
    query = update.callback_query

    # Seleccionar bloque
    if data.startswith("bloque_"):
        bloque_id = int(data.replace("bloque_", ""))
        await seleccionar_bloque_callback(update, context, bloque_id)
        return True

    # Ver imagen de requisición (nuevo)
    if data.startswith("ver_img_"):
        req_id = data.replace("ver_img_", "")
        await ver_imagen_requisicion_callback(update, context, req_id)
        return True

    # Ver requisición
    if data.startswith("ver_req_"):
        req_id = data.replace("ver_req_", "")
        await ver_requisicion_command_callback(update, context, req_id)
        return True
        
    # Cancelar requisición
    if data.startswith("cancelar_req_"):
        token_publico = data.replace("cancelar_req_", "")
        await cancelar_requisicion_callback(update, context, token_publico)
        return True

    # Aprobar como supervisor
    elif data.startswith("aprobar_sup_"):
        req_id = data.replace("aprobar_sup_", "")
        await aprobar_supervisor_callback(update, context, req_id)
        return True

    # Aprobar como directivo
    elif data.startswith("aprobar_dir_"):
        req_id = data.replace("aprobar_dir_", "")
        await aprobar_directivo_callback(update, context, req_id)
        return True

    # Rechazar
    elif data.startswith("rechazar_"):
        req_id = data.replace("rechazar_", "")
        await rechazar_callback(update, context, req_id)
        return True

    # Marcar como surtida
    elif data.startswith("surtir_"):
        req_id = data.replace("surtir_", "")
        await surtir_callback(update, context, req_id)
        return True

    # Cerrar requisición
    elif data.startswith("cerrar_"):
        req_id = data.replace("cerrar_", "")
        await cerrar_callback(update, context, req_id)
        return True

    # Seleccionar supervisor
    elif data.startswith("supervisor_"):
        supervisor = data.replace("supervisor_", "")
        await seleccionar_supervisor_callback(update, context, supervisor)
        return True

    # Seleccionar especialidad
    elif data.startswith("especialidad_"):
        especialidad = data.replace("especialidad_", "")
        await seleccionar_especialidad_callback(update, context, especialidad)
        return True

    # Ubicación No Aplica - DESPUES de tener obra
    elif data == "ubicacion_na":
        query = update.callback_query
        await query.answer()
        temp_req = UserSession.get_temp_requisicion(context) or {}
        
        # Verificar que ya tengamos la obra
        if not temp_req.get('obra'):
            await query.edit_message_text("❌ Error: Primero debes ingresar la obra", parse_mode='Markdown')
            return True
            
        temp_req['ubicacion'] = "NA"
        UserSession.set_temp_requisicion(context, temp_req)
        UserSession.set_user_state(context, 'esperando_supervisor')
        
        await query.edit_message_text("✅ Ubicación: *NA (No Aplica)*", parse_mode='Markdown')
        
        from Almacen.models.personal.personal import Empleado
        from asgiref.sync import sync_to_async
        supervisores = await sync_to_async(list)(Empleado.objects.filter(rol__in=['supervisor', 'directivo']))
        
        await update.effective_chat.send_message(
            text=Messages.NUEVA_REQUISICION_SUPERVISOR,
            parse_mode='Markdown',
            reply_markup=Keyboards.seleccionar_supervisor(supervisores)
        )
        return True

    # Fecha rápida seleccionada
    elif data.startswith("fecha_"):
        fecha_str = data.replace("fecha_", "")
        query = update.callback_query
        await query.answer()
        
        if fecha_str == "manual":
            await query.edit_message_text("Por favor, ingresa la fecha manualmente en formato DD/MM/YYYY:")
            UserSession.set_user_state(context, 'esperando_fecha_util')
        else:
            temp_req = UserSession.get_temp_requisicion(context)
            temp_req['fecha_util'] = fecha_str
            UserSession.set_temp_requisicion(context, temp_req)
            UserSession.set_user_state(context, 'esperando_especialidad')
            
            await query.edit_message_text(f"✅ Fecha seleccionada: *{fecha_str}*", parse_mode='Markdown')
            await update.effective_chat.send_message(
                text=Messages.NUEVA_REQUISICION_ESPECIALIDAD,
                parse_mode='Markdown',
                reply_markup=Keyboards.seleccionar_especialidad()
            )
        return True

    return False


async def ver_requisicion_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, req_id: str):
    """
    Callback para ver detalles de una requisición específica.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        req_id: ID de la requisición
    """
    from asgiref.sync import sync_to_async
    from django.core.exceptions import ObjectDoesNotExist
    
    query = update.callback_query
    await query.answer()

    try:
        # Obtener la requisición de forma asíncrona
        requisicion = await RequisicionService.obtener_requisicion(req_id)

        if not requisicion:
            await query.edit_message_text(
                "❌ No se encontró la requisición solicitada.",
                parse_mode='Markdown'
            )
            return
            
        # Asegurarse de que tenemos un objeto y no un coroutine
        if asyncio.iscoroutine(requisicion):
            requisicion = await requisicion
            
        # Cargar relaciones necesarias de forma asíncrona
        @sync_to_async
        def load_requisition_data(req_id):
            from Almacen.models.requisiciones.requisiciones import Requisicion
            try:
                return Requisicion.objects.select_related('bloque', 'solicitante', 'supervisor').get(id=req_id)
            except Requisicion.DoesNotExist:
                return None
                
        # Cargar la requisición con todas las relaciones necesarias
        requisicion = await load_requisition_data(req_id)
        if not requisicion:
            await query.edit_message_text(
                "❌ No se encontró la requisición solicitada.",
                parse_mode='Markdown'
            )
            return
            
        # Obtener información de roles del usuario
        user_data = UserSession.get_user_data(context)
        es_supervisor = user_data.get('es_supervisor', False)
        es_directivo = user_data.get('es_directivo', False)
        
        # Generar el mensaje con el formato adecuado de forma asíncrona
        @sync_to_async
        def get_formatted_message(requisicion):
            from Almacen.telegram_bot.base.messages import Messages
            return Messages.formato_requisicion(requisicion)
            
        mensaje = await get_formatted_message(requisicion)
        
        # Crear teclado según los permisos del usuario
        keyboard = []
        
        # Si es directivo y la requisición está pendiente de aprobación
        if es_directivo and requisicion.estado == 'supervisor':
            keyboard.append([
                InlineKeyboardButton(
                    "✅ Aprobar (Directivo)", 
                    callback_data=f"aprobar_dir_{requisicion.id}"
                )
            ])
            keyboard.append([
                InlineKeyboardButton(
                    "❌ Rechazar", 
                    callback_data=f"rechazar_{requisicion.id}"
                )
            ])
        
        # Si es supervisor y es el supervisor asignado
        elif es_supervisor and requisicion.supervisor and requisicion.supervisor.id == user_data.get('empleado_id'):
            if requisicion.estado == 'pendiente':
                keyboard.append([
                    InlineKeyboardButton(
                        "✅ Aprobar (Supervisor)", 
                        callback_data=f"aprobar_sup_{requisicion.id}"
                    )
                ])
                keyboard.append([
                    InlineKeyboardButton(
                        "❌ Rechazar", 
                        callback_data=f"rechazar_{requisicion.id}"
                    )
                ])
        
        # Botón para volver atrás
        keyboard.append([
            InlineKeyboardButton("🔙 Atrás", callback_data="pendientes_aprobacion"),
            InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_principal")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            mensaje,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error en ver_requisicion_command_callback: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Ocurrió un error al cargar la requisición.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_principal")]
            ])
        )


async def ver_imagen_requisicion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, req_id: str):
    """
    Callback para mostrar la imagen de una requisición.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        req_id: ID de la requisición
    """
    query = update.callback_query
    await query.answer()

    requisicion = await RequisicionService.obtener_requisicion(req_id)

    if not requisicion:
        await query.edit_message_text(
            Messages.REQUISICION_NO_ENCONTRADA.format(id=req_id),
            parse_mode='Markdown'
        )
        return

    # Verificar si tiene imagen
    if not requisicion.imagen or requisicion.imagen.name == 'requisiciones/default.jpg':
        await query.edit_message_text(
            f"❌ La requisición `{escape_markdown(req_id)}` no tiene imagen adjunta.",
            parse_mode='Markdown',
            reply_markup=Keyboards.volver_requisiciones()
        )
        return

    # Enviar la imagen con información de la requisición
    try:
        from django.conf import settings
        import os

        # Construir la ruta completa de la imagen
        image_path = os.path.join(settings.BASE_DIR, 'media', requisicion.imagen.name)

        # Verificar que el archivo existe
        if not os.path.exists(image_path):
            await query.edit_message_text(
                f"❌ No se encontró el archivo de imagen para la requisición `{escape_markdown(req_id)}`.",
                parse_mode='Markdown',
                reply_markup=Keyboards.volver_requisiciones()
            )
            return

        # Preparar el caption con información
        estado_emoji = {
            'pendiente': '🟡',
            'supervisor': '🟠',
            'autorizada': '🟢',
            'surtida': '🔵',
            'cerrada': '⚫',
            'rechazada': '🔴',
        }
        emoji = estado_emoji.get(requisicion.estado, '⚪')

        # Obtener el nombre del supervisor en contexto síncrono para evitar SynchronousOnlyOperation
        from asgiref.sync import sync_to_async
        from Almacen.models.requisiciones.requisiciones import Requisicion as ReqModel

        @sync_to_async
        def _get_supervisor_nombre(rid: str) -> str:
            try:
                req = ReqModel.objects.select_related('supervisor').get(id=rid)
                return req.supervisor.nombre if req.supervisor else 'Sin asignar'
            except ReqModel.DoesNotExist:
                return 'Sin asignar'

        supervisor_nombre = await _get_supervisor_nombre(req_id)

        caption = (
            f"{emoji} *Requisición:* `{escape_markdown(req_id)}`\n"
            f"*Obra:* {escape_markdown(requisicion.obra)}\n"
            f"*Ubicación:* {escape_markdown(requisicion.ubicacion)}\n"
            f"*Supervisor a cargo:* {escape_markdown(supervisor_nombre)}\n"
            f"*Estado:* {escape_markdown(requisicion.estado)}\n"
            f"*Fecha de creación:* {requisicion.fecha_soli}"
        )

        # Eliminar el mensaje anterior
        await query.message.delete()

        # Obtener información de roles del usuario y contexto
        user_data = UserSession.get_user_data(context)
        es_supervisor = user_data.get('es_supervisor', False)
        es_directivo = user_data.get('es_directivo', False)
        
        # Verificar si estamos en el contexto de "Mis Requisiciones"
        # Si es así, no mostrar botones de acción
        from_mis_requisiciones = context.user_data.get('from_mis_requisiciones', False)
        
        # Si estamos en "Mis Requisiciones", forzar show_actions=False
        if from_mis_requisiciones:
            es_supervisor = False
            es_directivo = False

        # Enviar la imagen
        with open(image_path, 'rb') as photo:
            await update.effective_chat.send_photo(
                photo=photo,
                caption=caption,
                parse_mode='Markdown',
                reply_markup=Keyboards.acciones_imagen_requisicion(
                    req_id, 
                    requisicion.estado,
                    es_supervisor=es_supervisor,
                    es_directivo=es_directivo
                )
            )

    except Exception as e:
        logger.error(f"Error al enviar imagen de requisición {req_id}: {e}", exc_info=True)
        await update.effective_chat.send_message(
            f"❌ Error al cargar la imagen de la requisición `{escape_markdown(req_id)}`\n\n"
            f"Error: {escape_markdown(str(e))}",
            parse_mode='Markdown',
            reply_markup=Keyboards.volver_requisiciones()
        )


async def aprobar_supervisor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, req_id: str):
    """
    Callback para aprobar una requisición como supervisor.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        req_id: ID de la requisición
    """
    from asgiref.sync import sync_to_async
    from Almacen.models.telegram_user import TelegramUser
    from Almacen.models.personal.personal import Empleado
    from Almacen.models.requisiciones.requisiciones import Requisicion
    
    query = update.callback_query
    await query.answer()
    
    try:
        # Obtener el usuario de Telegram y su perfil de empleado
        telegram_user = await UserSession.get_telegram_user(update)
        
        # Obtener empleado de forma asíncrona
        @sync_to_async
        def get_empleado():
            empleado = getattr(telegram_user, 'empleado', None)
            if not empleado:
                empleado = Empleado.objects.filter(telegram_id=telegram_user.telegram_id).first()
            return empleado
            
        empleado = await get_empleado()
        
        if not empleado:
            raise ValueError("No se encontró tu perfil de empleado. Asegúrate de que tu usuario de Telegram esté vinculado a un empleado en el sistema.")
                
        # Verificar que el empleado sea supervisor o directivo
        if empleado.rol not in ['supervisor', 'directivo']:
            raise ValueError("No tienes permisos para aprobar requisiciones.")
        
        # Función para verificar la requisición
        @sync_to_async
        def verificar_requisicion():
            try:
                requisicion = Requisicion.objects.get(id=req_id)
                
                # Agregar logs de depuración
                logger.info(f"[DEBUG] Intento de aprobación - Empleado ID: {empleado.id}, Rol: {empleado.rol}, Nombre: {empleado.nombre}")
                logger.info(f"[DEBUG] Supervisor asignado a la requisición: {'ID: ' + str(requisicion.supervisor.id) + ', Nombre: ' + requisicion.supervisor.nombre if requisicion.supervisor else 'Ninguno'}")
                
                # Verificar que el que aprueba sea el supervisor asignado o un directivo
                if empleado.rol == 'directivo':
                    logger.info("[DEBUG] Acceso concedido: Usuario es directivo")
                elif not requisicion.supervisor or requisicion.supervisor.id != empleado.id:
                    logger.warning(f"[DEBUG] Acceso denegado: El empleado {empleado.nombre} (ID: {empleado.id}) no es el supervisor asignado")
                    raise ValueError("No tienes permiso para aprobar esta requisición. Solo el supervisor asignado o un directivo pueden hacerlo.")
                else:
                    logger.info("[DEBUG] Acceso concedido: Usuario es el supervisor asignado")
                    
                return requisicion
                    
            except Requisicion.DoesNotExist:
                raise ValueError("La requisición no existe o ya ha sido eliminada.")
        
        # Ejecutar la verificación
        requisicion = await verificar_requisicion()
        
        # Función para aprobar la requisición
        @sync_to_async
        def aprobar_requisicion():
            return RequisicionService.aprobar_supervisor(req_id, supervisor=empleado)
        
        # Aprobar la requisición
        resultado = await aprobar_requisicion()

        if resultado.get('success'):
            mensaje = f"✅ *Requisición {req_id} aprobada por supervisor.*\n\n"
            mensaje += f"Estado actualizado a: *{resultado.get('requisicion').estado}*"
            
            # Verificar si el mensaje tiene texto antes de editarlo
            if query.message.text:
                await query.edit_message_text(mensaje, parse_mode='Markdown')
            else:
                await query.message.reply_text(mensaje, parse_mode='Markdown')
        else:
            error_msg = resultado.get('error', 'Error desconocido al aprobar la requisición')
            await query.message.reply_text(
                f"❌ *Error*: {escape_markdown(str(error_msg))}",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error en aprobar_supervisor_callback: {e}")
        error_msg = f"No se pudo aprobar la requisición: {str(e)}"
        
        if query.message.text:
            try:
                await query.edit_message_text(
                    f"❌ *Error*: {escape_markdown(str(e))}",
                    parse_mode='Markdown'
                )
            except:
                await query.message.reply_text(
                    f"❌ *Error*: {escape_markdown(str(e))}",
                    parse_mode='Markdown'
                )
        else:
            await query.message.reply_text(
                f"❌ *Error*: {escape_markdown(str(e))}",
                parse_mode='Markdown'
            )


async def aprobar_directivo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, req_id: str):
    """
    Callback para aprobar una requisición como directivo.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        req_id: ID de la requisición
    """
    from asgiref.sync import sync_to_async
    from Almacen.models.telegram_user import TelegramUser
    from Almacen.models.personal.personal import Empleado
    from Almacen.models.requisiciones.requisiciones import Requisicion
    
    query = update.callback_query
    await query.answer()
    
    try:
        # Obtener el usuario de Telegram y su perfil de empleado
        telegram_user = await UserSession.get_telegram_user(update)
        
        # Obtener empleado de forma asíncrona
        @sync_to_async
        def get_empleado():
            empleado = getattr(telegram_user, 'empleado', None)
            if not empleado:
                empleado = Empleado.objects.filter(telegram_id=telegram_user.telegram_id).first()
            return empleado
            
        empleado = await get_empleado()
        
        if not empleado:
            raise ValueError("No se encontró tu perfil de empleado. Asegúrate de que tu usuario de Telegram esté vinculado a un empleado en el sistema.")
                        
        # Verificar que el empleado sea directivo
        if empleado.rol != 'directivo':
            raise ValueError("Solo los directivos pueden aprobar requisiciones en esta etapa.")
        
        # Función para verificar la requisición
        @sync_to_async
        def verificar_requisicion():
            try:
                requisicion = Requisicion.objects.get(id=req_id)
                
                # Verificar que la requisición esté en el estado correcto
                if requisicion.estado != 'supervisor':
                    raise ValueError(f"La requisición debe estar en estado 'supervisor', actual: {requisicion.estado}")
                    
                # Verificar que el supervisor ya haya aprobado
                if not requisicion.autorizado_supervisor:
                    raise ValueError("El supervisor debe aprobar primero esta requisición.")
                    
                return requisicion
                    
            except Requisicion.DoesNotExist:
                raise ValueError("La requisición no existe o ya ha sido eliminada.")
        
        # Ejecutar la verificación
        requisicion = await verificar_requisicion()
        
        # Aprobar la requisición como directivo
        resultado = await RequisicionService.aprobar_directivo(req_id, usuario=telegram_user.user if hasattr(telegram_user, 'user') else None)

        if resultado.get('success'):
            mensaje = Messages.APROBACION_DIRECTIVO.format(
                id=req_id,
                folio=resultado.get('folio', 'N/A')
            )
            
            # Verificar si el mensaje tiene texto antes de editarlo
            if hasattr(query, 'message') and hasattr(query.message, 'text') and query.message.text:
                await query.edit_message_text(mensaje, parse_mode='Markdown')
            else:
                await query.message.reply_text(mensaje, parse_mode='Markdown')
        else:
            error_msg = resultado.get('error', 'Error desconocido al aprobar la requisición')
            await query.message.reply_text(
                f"❌ *Error*: {escape_markdown(str(error_msg))}",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error en aprobar_directivo_callback: {e}")
        error_msg = f"No se pudo aprobar la requisición: {str(e)}"
        
        if hasattr(query, 'message') and hasattr(query.message, 'text') and query.message.text:
            try:
                await query.edit_message_text(
                    f"❌ *Error*: {escape_markdown(str(e))}",
                    parse_mode='Markdown'
                )
            except:
                await query.message.reply_text(
                    f"❌ *Error*: {escape_markdown(str(e))}",
                    parse_mode='Markdown'
                )
        else:
            await query.message.reply_text(
                f"❌ *Error*: {escape_markdown(str(e))}",
                parse_mode='Markdown'
            )


async def rechazar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, req_id: str):
    """
    Callback para iniciar el proceso de rechazo de una requisición.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        req_id: ID de la requisición
    """
    from asgiref.sync import sync_to_async
    from Almacen.models.telegram_user import TelegramUser
    from Almacen.models.personal.personal import Empleado
    from Almacen.models.requisiciones.requisiciones import Requisicion
    
    query = update.callback_query
    await query.answer()
    
    try:
        # Obtener el usuario de Telegram y su perfil de empleado
        telegram_user = await UserSession.get_telegram_user(update)
        
        # Obtener empleado de forma asíncrona
        @sync_to_async
        def get_empleado():
            empleado = getattr(telegram_user, 'empleado', None)
            if not empleado:
                empleado = Empleado.objects.filter(telegram_id=telegram_user.telegram_id).first()
            return empleado
            
        empleado = await get_empleado()
        
        if not empleado:
            raise ValueError("No se encontró tu perfil de empleado. Asegúrate de que tu usuario de Telegram esté vinculado a un empleado en el sistema.")
                
        # Verificar que el empleado sea supervisor o directivo
        if empleado.rol not in ['supervisor', 'directivo']:
            raise ValueError("No tienes permisos para rechazar requisiciones.")
        
        # Función para verificar la requisición
        @sync_to_async
        def verificar_requisicion():
            try:
                requisicion = Requisicion.objects.get(id=req_id)
                
                # Verificar que la requisición no esté ya cerrada o rechazada
                if requisicion.estado in ["cerrada", "rechazada"]:
                    raise ValueError(f"La requisición ya está {requisicion.estado} y no puede ser rechazada.")
                
                # Agregar logs de depuración
                logger.info(f"[DEBUG] Intento de rechazo - Empleado ID: {empleado.id}, Rol: {empleado.rol}, Nombre: {empleado.nombre}")
                logger.info(f"[DEBUG] Supervisor asignado a la requisición: {'ID: ' + str(requisicion.supervisor.id) + ', Nombre: ' + requisicion.supervisor.nombre if requisicion.supervisor else 'Ninguno'}")
                
                # Verificar que el que rechaza sea el supervisor asignado o un directivo
                if empleado.rol == 'directivo':
                    logger.info("[DEBUG] Acceso concedido: Usuario es directivo")
                elif not requisicion.supervisor or requisicion.supervisor.id != empleado.id:
                    logger.warning(f"[DEBUG] Acceso denegado: El empleado {empleado.nombre} (ID: {empleado.id}) no es el supervisor asignado")
                    raise ValueError("No tienes permiso para rechazar esta requisición. Solo el supervisor asignado o un directivo pueden hacerlo.")
                else:
                    logger.info("[DEBUG] Acceso concedido: Usuario es el supervisor asignado")
                    
                return requisicion
                    
            except Requisicion.DoesNotExist:
                raise ValueError("La requisición no existe o ya ha sido eliminada.")
        
        # Ejecutar la verificación
        requisicion = await verificar_requisicion()
        
        # Si todo está bien, solicitar el motivo del rechazo
        UserSession.set_user_state(context, f'rechazando_{req_id}')
        
        if query.message.text:
            await query.edit_message_text(
                "✏️ *Rechazar Requisición*\n\n"
                f"ID: `{req_id}`\n"
                "Por favor, escribe el motivo del rechazo:",
                parse_mode='Markdown',
                reply_markup=Keyboards.cancelar()
            )
        else:
            await query.message.reply_text(
                "✏️ *Rechazar Requisición*\n\n"
                f"ID: `{req_id}`\n"
                "Por favor, escribe el motivo del rechazo:",
                parse_mode='Markdown',
                reply_markup=Keyboards.cancelar()
            )
            
    except Exception as e:
        logger.error(f"Error en rechazar_callback: {e}")
        if query.message.text:
            try:
                await query.edit_message_text(
                    f"❌ *Error*: {escape_markdown(str(e))}",
                    parse_mode='Markdown'
                )
            except:
                await query.message.reply_text(
                    f"❌ *Error*: {escape_markdown(str(e))}",
                    parse_mode='Markdown'
                )
        else:
            await query.message.reply_text(
                f"❌ *Error*: {escape_markdown(str(e))}",
                parse_mode='Markdown'
            )


async def surtir_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, req_id: str):
    """
    Callback para marcar una requisición como surtida.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        req_id: ID de la requisición
    """
    query = update.callback_query
    await query.answer()

    resultado = RequisicionService.marcar_surtida(req_id)

    if resultado['success']:
        await query.edit_message_text(
            f"✅ Requisición {req_id} marcada como surtida.",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            Messages.ERROR_GENERICO.format(error=escape_markdown(resultado['error'])),
            parse_mode='Markdown'
        )


async def cerrar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, req_id: str):
    """
    Callback para cerrar una requisición.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        req_id: ID de la requisición
    """
    query = update.callback_query
    await query.answer()

    resultado = RequisicionService.cerrar(req_id)

    if resultado['success']:
        await query.edit_message_text(
            f"✅ Requisición {req_id} cerrada.",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            Messages.ERROR_GENERICO.format(error=escape_markdown(resultado['error'])),
            parse_mode='Markdown'
        )


async def seleccionar_bloque_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, bloque_id: int):
    """
    Callback para seleccionar un bloque en la creación de requisición.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        bloque_id: ID del bloque seleccionado
    """
    from asgiref.sync import sync_to_async
    from Almacen.models.base.base import Bloque
    
    query = update.callback_query
    await query.answer()

    # Obtener el bloque seleccionado
    try:
        bloque = await sync_to_async(Bloque.objects.get)(id=bloque_id)
    except Bloque.DoesNotExist:
        await query.edit_message_text(
            "❌ Error: El bloque seleccionado no existe.",
            parse_mode='Markdown'
        )
        return

    temp_req = UserSession.get_temp_requisicion(context) or {}
    temp_req['bloque_id'] = bloque_id
    temp_req['ubicacion'] = bloque.nombre  # Guardar también el nombre
    UserSession.set_temp_requisicion(context, temp_req)
    UserSession.set_user_state(context, 'esperando_obra')

    # Confirmar selección
    await query.edit_message_text(
        f"✅ Bloque/Ubicación seleccionado: *{escape_markdown(bloque.nombre)}*",
        parse_mode='Markdown'
    )

    # Pedir nombre de la obra
    await update.effective_chat.send_message(
        text=Messages.NUEVA_REQUISICION_OBRA,
        parse_mode='Markdown',
        reply_markup=Keyboards.cancelar()
    )


async def seleccionar_supervisor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, supervisor: str):
    """
    Callback para seleccionar un supervisor en la creación de requisición.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        supervisor: ID del supervisor seleccionado
    """
    query = update.callback_query
    await query.answer()

    try:
        # Obtener el empleado (supervisor) por su ID
        supervisor_id = int(supervisor)
        from Almacen.models.personal.personal import Empleado
        empleado_supervisor = await sync_to_async(
            Empleado.objects.get
        )(id=supervisor_id)
        supervisor_nombre = empleado_supervisor.nombre
    except (ValueError, Exception) as e:
        logger.error(f"Error al obtener supervisor: {e}")
        await query.edit_message_text(
            "❌ Error al seleccionar el supervisor. Intenta nuevamente.",
            parse_mode='Markdown'
        )
        return

    temp_req = UserSession.get_temp_requisicion(context) or {}
    temp_req['supervisor'] = supervisor_id  # Store the ID instead of the name
    temp_req['supervisor_nombre'] = supervisor_nombre  # Store the name separately if needed
    UserSession.set_temp_requisicion(context, temp_req)
    UserSession.set_user_state(context, 'esperando_fecha_util')

    # Confirmar selección y pedir fecha
    await query.edit_message_text(
        f"✅ Supervisor seleccionado: *{escape_markdown(supervisor_nombre)}*",
        parse_mode='Markdown'
    )

    # Enviar nuevo mensaje para la fecha con botones rápidos
    await update.effective_chat.send_message(
        text=Messages.obtener_mensaje_fecha_util(),
        parse_mode='Markdown',
        reply_markup=Keyboards.fecha_rapida()
    )





async def seleccionar_especialidad_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, especialidad: str):
    """
    Callback para seleccionar una especialidad, mostrar mensaje con enlace
    y continuar al paso de subir imagen.
    """
    query = update.callback_query
    await query.answer()

    # Guardar la especialidad en el contexto temporal
    temp_req = UserSession.get_temp_requisicion(context) or {}
    temp_req['especialidad'] = especialidad
    UserSession.set_temp_requisicion(context, temp_req)

    # Crear requisición inmediatamente
    try:
        telegram_user = await UserSession.get_telegram_user(update)
        await query.edit_message_text("⏳ Creando requisición...")
        
        requisicion = await RequisicionService.crear_requisicion(
            obra=temp_req.get('obra'),
            ubicacion=temp_req.get('ubicacion'),
            especialidad=temp_req.get('especialidad'),
            supervisor_id=temp_req.get('supervisor'),
            fecha_util=temp_req.get('fecha_util'),
            solicitante_nombre=temp_req.get('solicitante_nombre'),
            bloque_id=temp_req.get('bloque_id'),
            telegram_user=telegram_user,
            imagen=None
        )
        
        from django.conf import settings
        import os
        dreacht_hub_url = os.getenv('DREACHT_HUB_URL', getattr(settings, 'DREACHT_HUB_URL', 'http://localhost:8001'))
        link = f"{dreacht_hub_url}/requisiciones/edit/{requisicion.token_publico}/"
        
        msg = f"✅ *Requisición Creada*\n\n*ID:* `{requisicion.id}`\n*Solicitante:* {escape_markdown(temp_req.get('solicitante_nombre'))}\n*Obra:* {escape_markdown(requisicion.obra)}\n\n🔗 Completa en:\n{link}"
        
        if 'localhost' not in link:
            kb = [[InlineKeyboardButton("🔗 Completar", url=link)], [InlineKeyboardButton("🏠 Menú", callback_data="limpiar_y_menu")]]
        else:
            kb = [[InlineKeyboardButton("🏠 Menú", callback_data="limpiar_y_menu")]]
        
        await update.effective_chat.send_message(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        UserSession.clear_user_state(context)
        UserSession.clear_temp_requisicion(context)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.effective_chat.send_message(f"❌ Error: {escape_markdown(str(e))}")

    # Limpiar cualquier mensaje auxiliar previo en contexto si existe
    if 'mensajes' in context.user_data:
        del context.user_data['mensajes']


async def cancelar_requisicion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, token_publico: str):
    """
    Callback para cancelar una requisición recién creada.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        token_publico: Token público de la requisición a cancelar
    """
    query = update.callback_query
    await query.answer()
    
    try:
        # Buscar la requisición por su token público
        try:
            requisicion = await sync_to_async(Requisicion.objects.get)(token_publico=token_publico)
        except Requisicion.DoesNotExist:
            await query.edit_message_text(
                "❌ No se encontró la requisición a cancelar.",
                parse_mode='Markdown'
            )
            return
            
        # Verificar que la requisición esté en estado pendiente
        if requisicion.estado != 'P':
            await query.edit_message_text(
                "⚠️ Solo se pueden cancelar requisiciones en estado pendiente.",
                parse_mode='Markdown'
            )
            return
            
        # Marcar como cancelada
        requisicion.estado = 'C'  # C = Cancelada
        await sync_to_async(requisicion.save)()
        
        # Actualizar el mensaje
        mensaje = (
            f"❌ *Requisición cancelada* `{token_publico}`\n\n"
            "La requisición ha sido cancelada correctamente."
        )
        
        # Crear teclado para volver al menú principal
        keyboard = [
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu_principal")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            mensaje,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error al cancelar la requisición: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Ocurrió un error al intentar cancelar la requisición. Por favor, inténtalo de nuevo.",
            parse_mode='Markdown'
        )


# ============================================================================
# HANDLERS DE MENSAJES PARA CONVERSACIONES DE REQUISICIONES
# ============================================================================

async def handle_requisicion_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str, text: str) -> bool:
    """
    Maneja mensajes de texto en conversaciones relacionadas con requisiciones.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        state: Estado actual del usuario
        text: Texto del mensaje

    Returns:
        bool: True si el mensaje fue manejado, False en caso contrario
    """
    # Flujo de creación de requisición
    if state == 'esperando_solicitante':
        await handle_esperando_solicitante(update, context, text)
        return True

    elif state == 'esperando_obra':
        await handle_esperando_obra(update, context, text)
        return True

    elif state == 'esperando_fecha_util':
        await handle_esperando_fecha_util(update, context, text)
        return True

    elif state == 'esperando_especialidad':
        await handle_esperando_especialidad(update, context, text)
        return True

    elif state == 'esperando_imagen':
        await handle_esperando_imagen(update, context, text)
        return True

    # Flujo de rechazo
    elif state and state.startswith('rechazando_'):
        await handle_rechazo(update, context, state, text)
        return True

    return False


async def handle_esperando_obra(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    Maneja el paso de ingresar la obra en la creación de requisición.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        text: Nombre de la obra
    """
    temp_req = UserSession.get_temp_requisicion(context) or {}
    temp_req['obra'] = text
    UserSession.set_temp_requisicion(context, temp_req)
    UserSession.set_user_state(context, 'esperando_supervisor')

    # Obtener supervisores desde BD
    supervisores = await CatalogoService.listar_supervisores()

    await update.message.reply_text(
        Messages.NUEVA_REQUISICION_SUPERVISOR,
        parse_mode='Markdown',
        reply_markup=Keyboards.seleccionar_supervisor(supervisores)
    )


async def handle_esperando_fecha_util(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    Maneja el paso de ingresar la fecha a utilizar en la creación de requisición.

    Validaciones:
    - Formato DD/MM/YYYY
    - No anterior a la fecha de creación (hoy)
    - No más de 2 semanas a futuro

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        text: Fecha en formato DD/MM/YYYY
    """
    from datetime import datetime, timedelta, date
    
    # 1️⃣ Validar formato de fecha
    try:
        fecha_ingresada = datetime.strptime(text, '%d/%m/%Y').date()
    except ValueError:
        fecha_actual = date.today().strftime("%d/%m/%Y")
        await update.message.reply_text(
            f"❌ *Formato de fecha inválido*\n\n"
            f"Debes ingresar en formato DD/MM/YYYY\n"
            f"*Ejemplo:* 25/12/2024\n\n"
            f"Hoy es: {fecha_actual}",
            parse_mode='Markdown',
            reply_markup=Keyboards.cancelar()
        )
        return

    # 2️⃣ Validar que no sea anterior a hoy (fecha de creación)
    fecha_hoy = date.today()
    if fecha_ingresada < fecha_hoy:
        fecha_actual_fmt = fecha_hoy.strftime("%d/%m/%Y")
        fecha_ingresada_fmt = fecha_ingresada.strftime("%d/%m/%Y")
        await update.message.reply_text(
            f"❌ *Fecha no válida*\n\n"
            f"La fecha ingresada ({fecha_ingresada_fmt}) es anterior a hoy.\n\n"
            f"*Hoy es:* {fecha_actual_fmt}\n\n"
            f"Por favor, selecciona una fecha igual o posterior.",
            parse_mode='Markdown',
            reply_markup=Keyboards.cancelar()
        )
        return

    # 3️⃣ Validar que no supere 2 semanas a futuro
    fecha_maxima = fecha_hoy + timedelta(days=14)
    if fecha_ingresada > fecha_maxima:
        fecha_actual_fmt = fecha_hoy.strftime("%d/%m/%Y")
        fecha_maxima_fmt = fecha_maxima.strftime("%d/%m/%Y")
        fecha_ingresada_fmt = fecha_ingresada.strftime("%d/%m/%Y")
        await update.message.reply_text(
            f"❌ *Fecha demasiado lejana*\n\n"
            f"La fecha ingresada ({fecha_ingresada_fmt}) supera el límite de 2 semanas.\n\n"
            f"*Hoy es:* {fecha_actual_fmt}\n"
            f"*Fecha máxima permitida:* {fecha_maxima_fmt}\n\n"
            f"Por favor, selecciona una fecha dentro de 2 semanas.",
            parse_mode='Markdown',
            reply_markup=Keyboards.cancelar()
        )
        return

    # ✅ Si pasa todas las validaciones, guardar la fecha
    temp_req = UserSession.get_temp_requisicion(context)
    temp_req['fecha_util'] = text
    UserSession.set_temp_requisicion(context, temp_req)
    UserSession.set_user_state(context, 'esperando_especialidad')

    await update.message.reply_text(
        Messages.NUEVA_REQUISICION_ESPECIALIDAD,
        parse_mode='Markdown',
        reply_markup=Keyboards.seleccionar_especialidad()
    )


async def handle_esperando_especialidad(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    Maneja el paso de ingresar la especialidad y CREA la requisición.
    Ya no pide imagen - el usuario completa en Dreacht Hub.
    """
    temp_req = UserSession.get_temp_requisicion(context)
    temp_req['especialidad'] = text
    UserSession.set_temp_requisicion(context, temp_req)
    
    # Crear la requisición inmediatamente (sin imagen)
    try:
        telegram_user = await UserSession.get_telegram_user(update)
        
        await update.message.reply_text(
            "⏳ Creando requisición...",
            parse_mode='Markdown'
        )
        
        requisicion = await RequisicionService.crear_requisicion(
            obra=temp_req.get('obra'),
            ubicacion=temp_req.get('ubicacion'),
            especialidad=temp_req.get('especialidad'),
            supervisor_id=temp_req.get('supervisor'),
            fecha_util=temp_req.get('fecha_util'),
            solicitante_nombre=temp_req.get('solicitante_nombre'),
            bloque_id=temp_req.get('bloque_id'),
            telegram_user=telegram_user,
            imagen=None
        )
        
        # Generar enlace Dreacht Hub
        from django.conf import settings
        import os
        dreacht_hub_url = os.getenv('DREACHT_HUB_URL', getattr(settings, 'DREACHT_HUB_URL', 'http://localhost:8001'))
        completion_link = f"{dreacht_hub_url}/requisiciones/edit/{requisicion.token_publico}/"
        
        # Mensaje de éxito
        mensaje = (
            f"✅ *Requisición Creada*\n\n"
            f"*ID:* `{requisicion.id}`\n"
            f"*Solicitante:* {escape_markdown(temp_req.get('solicitante_nombre', 'N/A'))}\n"
            f"*Obra:* {escape_markdown(requisicion.obra)}\n"
            f"*Ubicación:* {escape_markdown(requisicion.ubicacion)}\n"
            f"*Supervisor:* {escape_markdown(temp_req.get('supervisor_nombre', 'N/A'))}\n"
            f"*Fecha:* {temp_req.get('fecha_util', 'N/A')}\n"
            f"*Especialidad:* {escape_markdown(requisicion.especialidad)}\n\n"
            f"🔗 *Completa tu requisición:*\n"
            f"{completion_link}\n\n"
            f"👆 Abre el enlace para:\n"
            f"• Agregar productos\n"
            f"• Generar PDF\n"
            f"• Finalizar requisición"
        )
        
        # Botón solo si NO es localhost
        if 'localhost' not in completion_link and '127.0.0.1' not in completion_link:
            keyboard = [
                [InlineKeyboardButton("🔗 Completar Requisición", url=completion_link)],
                [InlineKeyboardButton("🏠 Menú", callback_data="limpiar_y_menu")]
            ]
        else:
            keyboard = [[InlineKeyboardButton("🏠 Menú", callback_data="limpiar_y_menu")]]
        
        await update.message.reply_text(
            mensaje,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        UserSession.clear_user_state(context)
        UserSession.clear_temp_requisicion(context)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error: {escape_markdown(str(e))}\n\nIntenta con /nueva",
            parse_mode='Markdown'
        )
        UserSession.clear_user_state(context)
        UserSession.clear_temp_requisicion(context)


async def handle_esperando_imagen(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str = None):
    """
    Maneja el paso de subir una imagen en la creación de requisición.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        text: Texto enviado por el usuario (opcional)
    """
    # Verificar si se envió una foto
    if update.message.photo:
        try:
            # Obtener la foto de mayor resolución
            photo = update.message.photo[-1]
            file_id = photo.file_id
            
            # Obtener la requisición temporal
            temp_req = UserSession.get_temp_requisicion(context) or {}
            
            # Guardar el ID de la imagen en la requisición
            from .services_requisiciones import RequisicionService
            await RequisicionService.actualizar_imagen(
                token_publico=temp_req.get('token_publico'),
                imagen_id=file_id,
                telegram_user=await UserSession.get_telegram_user(update)
            )
            
            # Confirmar recepción de la imagen
            await update.message.reply_text(
                "✅ Imagen recibida correctamente. Procesando requisición...",
                parse_mode='Markdown'
            )
            
            # Mensaje de confirmación final
            await update.message.reply_text(
                "✅ Requisición creada exitosamente.\n\n"
                "Puedes ver el estado de tus requisiciones con el comando /misrequisiciones",
                parse_mode='Markdown'
            )
            
            # Limpiar el estado
            UserSession.clear_temp_requisicion(context)
            UserSession.clear_user_state(context)
            
        except Exception as e:
            logger.error(f"Error al procesar la imagen: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Ocurrió un error al procesar la imagen. Por favor, inténtalo de nuevo.",
                parse_mode='Markdown'
            )
    
    # Si se envía texto, verificar si es /skip
    elif text and text.lower() == '/skip':
        # Continuar sin imagen
        await update.message.reply_text(
            "✅ Continuando sin imagen. Procesando requisición...",
            parse_mode='Markdown'
        )
        
        # Mensaje de confirmación final
        await update.message.reply_text(
            "✅ Requisición creada exitosamente sin imagen.\n\n"
            "Puedes ver el estado de tus requisiciones con el comando /misrequisiciones",
            parse_mode='Markdown'
        )
        
        # Limpiar el estado
        UserSession.clear_temp_requisicion(context)
        UserSession.clear_user_state(context)
    
    # Si se envía texto que no es /skip
    else:
        await update.message.reply_text(
            "❌ Por favor, envía una imagen de la requisición o escribe /skip para continuar sin imagen.\n\n"
            "Puedes tomar una foto directamente desde la cámara o subir una existente.",
            parse_mode='Markdown',
            reply_markup=Keyboards.esperando_imagen()
        )


async def handle_esperando_solicitante(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    Maneja el paso de ingresar el solicitante en la creación de requisición.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        text: Nombre del solicitante
    """
    temp_req = UserSession.get_temp_requisicion(context) or {}
    temp_req['solicitante_nombre'] = text
    UserSession.set_temp_requisicion(context, temp_req)
    UserSession.set_user_state(context, 'esperando_bloque')

    # Obtener bloques disponibles
    bloques = await CatalogoService.obtener_bloques()
    
    if not bloques:
        await update.message.reply_text(
            "❌ No hay bloques registrados en el sistema.\n\n"
            "Por favor, contacta al administrador para registrar bloques.",
            parse_mode='Markdown'
        )
        UserSession.clear_user_state(context)
        UserSession.clear_temp_requisicion(context)
        return

    await update.message.reply_text(
        "*Paso 2:* Selecciona el bloque/ubicación:",
        parse_mode='Markdown',
        reply_markup=Keyboards.seleccionar_bloque(bloques)
    )


async def handle_rechazo(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str, text: str):
    """
    Maneja el proceso de rechazo de una requisición.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        state: Estado que incluye el ID de la requisición
        text: Motivo del rechazo
    """
    from asgiref.sync import sync_to_async
    from Almacen.models.telegram_user import TelegramUser
    from Almacen.models.personal.personal import Empleado
    from Almacen.models.requisiciones.requisiciones import Requisicion
    
    req_id = state.replace('rechazando_', '')
    motivo = text.strip()
    
    if not motivo:
        await update.message.reply_text(
            "❌ El motivo del rechazo no puede estar vacío. Por favor, inténtalo de nuevo.",
            parse_mode='Markdown'
        )
        return
    
    try:
        # Obtener el usuario de Telegram y su perfil de empleado
        telegram_user = await UserSession.get_telegram_user(update)
        empleado = await sync_to_async(lambda: getattr(telegram_user, 'empleado', None))()
        
        if not empleado:
            # Intentar encontrar al empleado por el ID de Telegram
            empleado = await sync_to_async(Empleado.objects.filter(telegram_id=telegram_user.telegram_id).first)()
            
            if not empleado:
                raise ValueError("No se encontró tu perfil de empleado. No puedes rechazar la requisición.")
        
        # Llamar al servicio de rechazo
        resultado = await RequisicionService.rechazar(
            req_id=req_id,
            motivo=motivo,
            usuario=empleado  # Pasamos el empleado como usuario que realiza el rechazo
        )

        if resultado.get('success'):
            mensaje = (
                "❌ *Requisición Rechazada*\n\n"
                f"📋 *ID*: `{req_id}`\n"
                f"📝 *Motivo*: {escape_markdown(motivo)}\n"
                f"👤 *Rechazada por*: {escape_markdown(empleado.nombre) if empleado else 'Sistema'}\n\n"
                f"_Estado actualizado correctamente._"
            )
            
            # Limpiar el estado de la conversación
            UserSession.clear_user_state(context)
            
            # Obtener el menú principal
            menu_principal = Keyboards.menu_principal(
                es_supervisor=empleado.rol in ['supervisor', 'directivo'],
                es_directivo=empleado.rol == 'directivo'
            )
            
            # Enviar mensaje de confirmación al supervisor
            await update.message.reply_text(
                mensaje,
                parse_mode='Markdown',
                reply_markup=menu_principal
            )
            
            # Notificar al solicitante en segundo plano
            try:
                # Obtener la requisición de forma asíncrona
                requisicion_actual = await sync_to_async(Requisicion.objects.get)(id=req_id)
                # Obtener el solicitante
                solicitante = await sync_to_async(lambda: requisicion_actual.solicitante)()
                
                if solicitante and getattr(solicitante, 'telegram_id', None):
                    mensaje_solicitante = (
                        "📢 *Notificación de Rechazo*\n\n"
                        f"Tu requisición *{req_id}* ha sido *rechazada*.\n"
                        f"📝 *Motivo*: {escape_markdown(motivo)}\n\n"
                        "_Por favor, revisa los detalles y realiza las correcciones necesarias._"
                    )
                    await context.bot.send_message(
                        chat_id=solicitante.telegram_id,
                        text=mensaje_solicitante,
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"Error al notificar al solicitante: {e}")
                # No romper el flujo principal si hay error en la notificación
        else:
            error_msg = resultado.get('error', 'Error desconocido al rechazar la requisición')
            await update.message.reply_text(
                f"❌ *Error*: {escape_markdown(str(error_msg))}",
                parse_mode='Markdown',
                reply_markup=Keyboards.menu_principal(
                    es_supervisor=empleado.rol in ['supervisor', 'directivo'] if empleado else False,
                    es_directivo=empleado.rol == 'directivo' if empleado else False
                )
            )
            
    except Requisicion.DoesNotExist:
        await update.message.reply_text(
            "❌ Error: La requisición no existe o ya ha sido eliminada.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error en handle_rechazo: {e}")
        await update.message.reply_text(
            f"❌ *Error*: {escape_markdown(str(e))}",
            parse_mode='Markdown'
        )

    UserSession.clear_user_state(context)
