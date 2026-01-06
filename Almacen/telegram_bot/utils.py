"""
Utilidades para el bot de Telegram.
"""
import logging
from typing import Optional, Dict, Any
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


from .sessions import UserSession

def require_auth(func):
    """
    Decorador para requerir autenticación en comandos.

    Args:
        func: Función a decorar

    Returns:
        Función decorada
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user

        if not user:
            await update.message.reply_text(
                "❌ No se pudo identificar al usuario."
            )
            return

        # Verificar si el usuario está registrado
        if not UserSession.is_user_registered(context):
            # Iniciar proceso de registro
            await start_registration(update, context)
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


def require_supervisor(func):
    """
    Decorador para requerir permisos de supervisor.

    Args:
        func: Función a decorar

    Returns:
        Función decorada
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        from Almacen.models.telegram_user import TelegramUser
        from django.contrib.auth.models import User
        
        user = update.effective_user
        
        # Verificar si el usuario está registrado en Telegram
        try:
            telegram_user = await sync_to_async(TelegramUser.objects.get)(telegram_id=user.id)
            empleado = await sync_to_async(lambda: telegram_user.empleado)()
            
            # Verificar si el empleado es supervisor o directivo
            if not empleado or not empleado.es_supervisor():
                await update.message.reply_text(
                    "⛔ No tienes permisos de supervisor para realizar esta acción.\n\n"
                    "Solo los supervisores y directivos pueden aprobar o rechazar requisiciones."
                )
                return
                
        except TelegramUser.DoesNotExist:
            await update.message.reply_text(
                "🔒 No estás registrado en el sistema. Por favor, regístrate primero."
            )
            return
        except Exception as e:
            logger.error(f"Error al verificar permisos de supervisor: {e}")
            await update.message.reply_text(
                "❌ Ocurrió un error al verificar tus permisos. Por favor, inténtalo de nuevo."
            )
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


def require_directivo(func):
    """
    Decorador para requerir permisos de directivo.

    Args:
        func: Función a decorar

    Returns:
        Función decorada
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user

        # TODO: Implementar verificación real de permisos de directivo
        # Debe consultar la base de datos para verificar roles/permisos del usuario
        # Por ahora, permitimos a todos para demo

        es_directivo = True  # Placeholder - implementar lógica real

        if not es_directivo:
            await update.message.reply_text(
                "⛔ No tienes permisos de directivo para realizar esta acción."
            )
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


def log_command(func):
    """
    Decorador para registrar el uso de comandos.
    
    Args:
        func: Función a decorar
        
    Returns:
        Función decorada
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        command = update.message.text if update.message else "callback"
        
        logger.info(
            f"Usuario {user.id} ({user.username or user.first_name}) "
            f"ejecutó: {command}"
        )
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def handle_errors(func):
    """
    Decorador para manejar errores en handlers.
    
    Args:
        func: Función a decorar
        
    Returns:
        Función decorada
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error en {func.__name__}: {e}", exc_info=True)
            
            error_message = (
                "❌ *Error*\n\n"
                f"Ocurrió un error al procesar tu solicitud:\n"
                f"`{str(e)}`\n\n"
                "Por favor, intenta nuevamente o contacta al administrador."
            )
            
            if update.message:
                await update.message.reply_text(
                    error_message,
                    parse_mode='Markdown'
                )
            elif update.callback_query and update.callback_query.message:
                await update.callback_query.message.reply_text(
                    error_message,
                    parse_mode='Markdown'
                )
            else:
                logger.error("No se pudo enviar mensaje de error: no hay forma de enviar mensaje")
    
    return wrapper


def format_date(date_obj) -> str:
    """
    Formatea una fecha para mostrar en Telegram.
    
    Args:
        date_obj: Objeto date o datetime
        
    Returns:
        Fecha formateada
    """
    if not date_obj:
        return "N/A"
    
    try:
        return date_obj.strftime("%d/%m/%Y")
    except:
        return str(date_obj)


def format_datetime(datetime_obj) -> str:
    """
    Formatea una fecha y hora para mostrar en Telegram.
    
    Args:
        datetime_obj: Objeto datetime
        
    Returns:
        Fecha y hora formateada
    """
    if not datetime_obj:
        return "N/A"
    
    try:
        return datetime_obj.strftime("%d/%m/%Y %H:%M")
    except:
        return str(datetime_obj)


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Trunca un texto si excede la longitud máxima.
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        
    Returns:
        Texto truncado
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def escape_markdown(text: str) -> str:
    """
    Escapa caracteres especiales de Markdown.
    
    Args:
        text: Texto a escapar
        
    Returns:
        Texto escapado
    """
    if not text:
        return ""
    
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def parse_command_args(text: str) -> list:
    """
    Parsea los argumentos de un comando.
    
    Args:
        text: Texto del comando
        
    Returns:
        Lista de argumentos
    """
    if not text:
        return []
    
    parts = text.split()
    
    # Remover el comando (primer elemento)
    if parts and parts[0].startswith('/'):
        parts = parts[1:]
    
    return parts


def get_user_mention(user) -> str:
    """
    Obtiene una mención formateada del usuario.

    Args:
        user: Objeto User de Telegram

    Returns:
        Mención formateada
    """
    if user.username:
        return f"@{user.username}"
    else:
        return user.first_name or f"Usuario {user.id}"


async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Inicia el proceso de registro para un nuevo usuario.
    Verifica automáticamente si el usuario está registrado como empleado.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
    """
    from asgiref.sync import sync_to_async
    from Almacen.models.telegram_user import TelegramUser
    from Almacen.models.personal.personal import Empleado
    from .base.keyboards import Keyboards

    try:
        # Obtener o crear usuario de Telegram
        telegram_user = await UserSession.get_telegram_user(update)

        # Función síncrona para obtener el empleado por telegram_id
        @sync_to_async
        def _get_empleado_por_telegram_id(telegram_id):
            """Obtiene el empleado por telegram_id en contexto síncrono."""
            try:
                return Empleado.objects.get(telegram_id=str(telegram_id))
            except Empleado.DoesNotExist:
                return None

        @sync_to_async
        def _asociar_empleado_si_falta(telegram_user, empleado):
            """Asocia el empleado al TelegramUser solo si no está ya asociado.

            Importante: usa empleado_id para evitar disparar consultas extra en contexto async.
            """
            # Si ya tiene empleado_id, no hacemos nada
            if getattr(telegram_user, 'empleado_id', None):
                return

            telegram_user.empleado = empleado
            telegram_user.save()

        try:
            # Buscar empleado por telegram_id usando función síncrona envuelta
            empleado = await _get_empleado_por_telegram_id(telegram_user.telegram_id)

            # Si encontramos el empleado, completar registro automáticamente
            if empleado:
                es_supervisor = empleado.rol in ['supervisor', 'directivo']
                es_directivo = empleado.rol == 'directivo'

                # Actualizar datos del usuario de Telegram
                if empleado.nombre:
                    name_parts = empleado.nombre.split()
                    telegram_user.first_name = name_parts[0] if name_parts else telegram_user.first_name
                    telegram_user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                    await sync_to_async(telegram_user.save)()

                # Asociar empleado al usuario de Telegram si no está ya asociado
                await _asociar_empleado_si_falta(telegram_user, empleado)

                # Guardar información de roles en la sesión
                UserSession.set_user_data(context, 'es_supervisor', es_supervisor)
                UserSession.set_user_data(context, 'es_directivo', es_directivo)
                UserSession.set_user_registered(context, True)
                UserSession.clear_user_state(context)

                # Determinar mensaje de bienvenida según el rol
                if es_directivo:
                    mensaje_bienvenida = "👔 *¡Bienvenido Director!*"
                elif es_supervisor:
                    mensaje_bienvenida = "👨‍💼 *¡Bienvenido Supervisor!*"
                else:
                    mensaje_bienvenida = "👤 *¡Bienvenido!*"

                # Mostrar mensaje de bienvenida
                mensaje = (
                    f"✅ *¡Registro automático exitoso!*\n\n"
                    f"{mensaje_bienvenida}\n"
                    f"Nombre: {escape_markdown(empleado.nombre or '')}\n"
                    f"Rol: {dict(Empleado.ROL_CHOICES).get(empleado.rol, empleado.rol)}\n"
                    f"ID de Telegram: `{telegram_user.telegram_id}`\n\n"
                    "¿En qué puedo ayudarte hoy?"
                )

                if update.callback_query:
                    await update.callback_query.message.reply_text(
                        mensaje,
                        parse_mode='Markdown',
                        reply_markup=await Keyboards.menu_principal(es_supervisor, es_directivo)
                    )
                else:
                    await update.message.reply_text(
                        mensaje,
                        parse_mode='Markdown',
                        reply_markup=await Keyboards.menu_principal(es_supervisor, es_directivo)
                    )
                return

        except Exception as e:
            logger.error(f"Error al verificar empleado: {str(e)}")
            # Continuar con el registro normal en caso de error

    except Exception as e:
        logger.error(f"Error en start_registration: {str(e)}")
        # Continuar con el registro normal en caso de error

    # Si llegamos aquí, continuar con el registro normal
    UserSession.set_user_state(context, 'esperando_nombre_registro')
    
    mensaje = (
        "👋 *¡Bienvenido al Bot de Requisiciones!*\n\n"
        "Parece que no estás registrado en el sistema o no tienes un perfil de empleado.\n\n"
        "Por favor, ingresa tu nombre completo para continuar:"
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            mensaje,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            mensaje,
            parse_mode='Markdown'
        )


async def complete_registration(update: Update, context: ContextTypes.DEFAULT_TYPE, nombre: str):
    """
    Completa el registro del usuario y verifica su rol.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        nombre: Nombre proporcionado por el usuario
    """
    from asgiref.sync import sync_to_async
    from Almacen.models.telegram_user import TelegramUser
    from .base.messages import Messages
    from .base.keyboards import Keyboards

    try:
        # Obtener o crear usuario de Telegram
        telegram_user = await UserSession.get_telegram_user(update)

        # Actualizar nombre si es necesario
        if nombre and nombre.strip():
            # Dividir el nombre en first_name y last_name
            partes = nombre.strip().split()
            if len(partes) >= 2:
                telegram_user.first_name = partes[0]
                telegram_user.last_name = " ".join(partes[1:])
            else:
                telegram_user.first_name = nombre.strip()
                telegram_user.last_name = ""

            await sync_to_async(telegram_user.save)()

        # Verificar si el usuario es empleado y su rol
        es_supervisor = False
        es_directivo = False
        mensaje_bienvenida = ""

        try:
            # Obtener el empleado asociado al usuario de Telegram
            empleado = await sync_to_async(lambda: getattr(telegram_user, 'empleado', None))()
            
            if empleado:
                es_supervisor = empleado.rol in ['supervisor', 'directivo']
                es_directivo = empleado.rol == 'directivo'
                
                if es_directivo:
                    mensaje_bienvenida = "👔 *¡Bienvenido Director!*"
                elif es_supervisor:
                    mensaje_bienvenida = "👨‍💼 *¡Bienvenido Supervisor!*"
                else:
                    mensaje_bienvenida = "👤 *¡Bienvenido!*"
            else:
                mensaje_bienvenida = "👤 *¡Bienvenido!*\n\n" \
                                   "Actualmente no estás registrado como empleado. " \
                                   "Contacta al administrador para obtener acceso a más funciones."

        except Exception as e:
            logger.error(f"Error al verificar rol de empleado: {e}")
            mensaje_bienvenida = "👤 *¡Bienvenido!*"

        # Guardar información de roles en la sesión
        UserSession.set_user_data(context, 'es_supervisor', es_supervisor)
        UserSession.set_user_data(context, 'es_directivo', es_directivo)
        UserSession.set_user_registered(context, True)
        UserSession.clear_user_state(context)

        # Mostrar mensaje de bienvenida personalizado
        await update.message.reply_text(
            f"✅ *¡Registro completado!*\n\n"
            f"{mensaje_bienvenida}\n\n"
            f"Nombre: {escape_markdown(telegram_user.nombre_completo_telegram)}\n"
            f"ID de Telegram: `{telegram_user.telegram_id}`\n\n"
            f"¿En qué puedo ayudarte hoy?",
            parse_mode='Markdown',
            reply_markup=await Keyboards.menu_principal(es_supervisor, es_directivo)
        )

    except Exception as e:
        logger.error(f"Error en registro: {e}")
        await update.message.reply_text(
            "❌ Error en el registro. Por favor, intenta nuevamente.",
            parse_mode='Markdown'
        )
