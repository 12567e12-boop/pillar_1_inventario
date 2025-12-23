"""
Utilidades específicas para la gestión de requisiciones en el bot de Telegram.

Este módulo contiene funciones auxiliares y helpers que son específicos
para el manejo de requisiciones y no aplican a otras funcionalidades.
"""
import logging
from typing import Optional, Dict, Any, List
from telegram import Update
from telegram.ext import ContextTypes

from .services_requisiciones import RequisicionService
from ..sessions import UserSession

logger = logging.getLogger(__name__)


def validar_requisicion_data(data: Dict[str, Any]) -> List[str]:
    """
    Valida los datos de una requisición antes de crearla.

    Args:
        data: Diccionario con los datos de la requisición

    Returns:
        Lista de errores de validación (vacía si es válida)
    """
    errores = []

    if not data.get('obra', '').strip():
        errores.append("La obra es obligatoria")

    if not data.get('ubicacion', '').strip():
        errores.append("La ubicación es obligatoria")

    if not data.get('especialidad', '').strip():
        errores.append("La especialidad es obligatoria")

    # Validar longitud máxima
    if len(data.get('obra', '')) > 200:
        errores.append("El nombre de la obra es demasiado largo (máx. 200 caracteres)")

    if len(data.get('ubicacion', '')) > 200:
        errores.append("La ubicación es demasiado larga (máx. 200 caracteres)")

    return errores


def formatear_requisicion_para_log(requisicion) -> str:
    """
    Formatea una requisición para logging.

    Args:
        requisicion: Objeto Requisicion

    Returns:
        String formateado para logs
    """
    return f"ID:{requisicion.id} Estado:{requisicion.estado} Obra:{requisicion.obra}"


def obtener_permisos_usuario_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Dict[str, bool]:
    """
    Determina los permisos del usuario de Telegram basado en su identidad.

    TODO: Implementar verificación real contra la base de datos de usuarios Django.
    Por ahora, retorna permisos de demo.

    Args:
        update: Update de Telegram
        context: Contexto de la conversación

    Returns:
        Dict con permisos del usuario
    """
    user = update.effective_user

    # TODO: Implementar lógica real de permisos
    # Por ejemplo:
    # - Verificar si el telegram_id está vinculado a un usuario Django
    # - Consultar roles/permisos del usuario en la base de datos
    # - Cachear permisos para evitar consultas repetidas

    # Permisos de demo - TODOS TIENEN ACCESO
    return {
        'es_supervisor': True,
        'es_directivo': True,
        'puede_crear': True,
        'puede_ver_todas': True,
    }


def puede_aprobar_requisicion(user_permisos: Dict[str, bool], estado_actual: str) -> bool:
    """
    Determina si un usuario puede aprobar una requisición en su estado actual.

    Args:
        user_permisos: Permisos del usuario
        estado_actual: Estado actual de la requisición

    Returns:
        True si puede aprobar, False en caso contrario
    """
    if estado_actual == 'pendiente' and user_permisos.get('es_supervisor', False):
        return True

    if estado_actual == 'supervisor' and user_permisos.get('es_directivo', False):
        return True

    return False


def puede_rechazar_requisicion(user_permisos: Dict[str, bool], estado_actual: str) -> bool:
    """
    Determina si un usuario puede rechazar una requisición en su estado actual.

    Args:
        user_permisos: Permisos del usuario
        estado_actual: Estado actual de la requisición

    Returns:
        True si puede rechazar, False en caso contrario
    """
    # Solo supervisores y directivos pueden rechazar
    if not (user_permisos.get('es_supervisor', False) or user_permisos.get('es_directivo', False)):
        return False

    # No se puede rechazar si ya está cerrada o rechazada
    if estado_actual in ['cerrada', 'rechazada']:
        return False

    return True


def puede_marcar_surtida(user_permisos: Dict[str, bool], estado_actual: str) -> bool:
    """
    Determina si un usuario puede marcar una requisición como surtida.

    Args:
        user_permisos: Permisos del usuario
        estado_actual: Estado actual de la requisición

    Returns:
        True si puede marcar como surtida, False en caso contrario
    """
    # Solo usuarios autorizados pueden marcar como surtida
    # TODO: Definir permisos específicos para surtido
    return estado_actual == 'autorizada' and user_permisos.get('puede_crear', False)


def puede_cerrar_requisicion(user_permisos: Dict[str, bool], estado_actual: str) -> bool:
    """
    Determina si un usuario puede cerrar una requisición.

    Args:
        user_permisos: Permisos del usuario
        estado_actual: Estado actual de la requisición

    Returns:
        True si puede cerrar, False en caso contrario
    """
    # Solo usuarios autorizados pueden cerrar
    # TODO: Definir permisos específicos para cierre
    return estado_actual == 'surtida' and user_permisos.get('puede_crear', False)


def limpiar_datos_temporales_requisicion(context: ContextTypes.DEFAULT_TYPE):
    """
    Limpia todos los datos temporales relacionados con requisiciones.

    Args:
        context: Contexto de la conversación
    """
    UserSession.clear_user_state(context)
    UserSession.clear_temp_requisicion(context)

    # Limpiar cualquier otro dato temporal específico de requisiciones
    user_data = UserSession.get_user_data(context)
    keys_to_remove = [k for k in user_data.keys() if k.startswith('req_')]
    for key in keys_to_remove:
        del user_data[key]


def log_accion_requisicion(accion: str, req_id: str, user_id: Optional[int] = None, exito: bool = True):
    """
    Registra una acción realizada sobre una requisición.

    Args:
        accion: Tipo de acción (aprobar, rechazar, crear, etc.)
        req_id: ID de la requisición
        user_id: ID del usuario de Telegram (opcional)
        exito: Si la acción fue exitosa
    """
    status = "EXITOSA" if exito else "FALLIDA"
    logger.info(f"ACCIÓN {status}: {accion.upper()} en requisición {req_id} por usuario {user_id or 'N/A'}")


def generar_mensaje_confirmacion_accion(accion: str, req_id: str, requisicion) -> str:
    """
    Genera un mensaje de confirmación para una acción sobre una requisición.

    Args:
        accion: Tipo de acción
        req_id: ID de la requisición
        requisicion: Objeto Requisicion

    Returns:
        Mensaje de confirmación formateado
    """
    acciones = {
        'aprobar_supervisor': f"¿Aprobar como supervisor la requisición {req_id}?",
        'aprobar_directivo': f"¿Aprobar como directivo la requisición {req_id}?",
        'rechazar': f"¿Rechazar la requisición {req_id}?",
        'surtir': f"¿Marcar como surtida la requisición {req_id}?",
        'cerrar': f"¿Cerrar la requisición {req_id}?",
    }

    base_msg = acciones.get(accion, f"¿Confirmar acción '{accion}' en requisición {req_id}?")

    if requisicion:
        base_msg += f"\n\nObra: {escape_markdown(requisicion.obra)}"
        base_msg += f"\nEstado actual: {escape_markdown(requisicion.estado)}"

    return base_msg


def validar_transicion_estado(estado_actual: str, estado_nuevo: str) -> bool:
    """
    Valida si una transición de estado es permitida.

    Args:
        estado_actual: Estado actual de la requisición
        estado_nuevo: Estado al que se quiere cambiar

    Returns:
        True si la transición es válida, False en caso contrario
    """
    transiciones_validas = {
        'pendiente': ['supervisor', 'rechazada'],
        'supervisor': ['autorizada', 'rechazada'],
        'autorizada': ['surtida', 'rechazada'],
        'surtida': ['cerrada'],
        'rechazada': [],  # No se puede cambiar de rechazada
        'cerrada': [],    # No se puede cambiar de cerrada
    }

    return estado_nuevo in transiciones_validas.get(estado_actual, [])


def obtener_requisiciones_usuario(user_id: int, estado: Optional[str] = None, limit: int = 10) -> List:
    """
    Obtiene las requisiciones asociadas a un usuario de Telegram.

    TODO: Implementar vinculación real entre telegram_id y usuario Django.

    Args:
        user_id: ID del usuario de Telegram
        estado: Filtrar por estado (opcional)
        limit: Número máximo de resultados

    Returns:
        Lista de requisiciones
    """
    # TODO: Implementar lógica real para obtener requisiciones del usuario
    # Por ahora, retorna todas las requisiciones
    return RequisicionService.listar_requisiciones(estado=estado)[:limit]


def formatear_lista_requisiciones_para_telegram(requisiciones: List) -> str:
    """
    Formatea una lista de requisiciones para mostrar en Telegram.

    Args:
        requisiciones: Lista de requisiciones

    Returns:
        Mensaje formateado en Markdown
    """
    if not requisiciones:
        return "📭 No tienes requisiciones registradas."

    mensaje = "📋 *Tus Requisiciones:*\n\n"

    for req in requisiciones[:10]:  # Limitar a 10 para no saturar
        estado_emoji = {
            'pendiente': '🟡',
            'supervisor': '🟠',
            'autorizada': '🟢',
            'surtida': '🔵',
            'cerrada': '⚫',
            'rechazada': '🔴',
        }
        emoji = estado_emoji.get(req.estado, '⚪')

        mensaje += f"{emoji} `{escape_markdown(req.id or 'SIN-ID')}` - {escape_markdown(req.obra)}\n"
        mensaje += f"   Estado: {escape_markdown(req.estado)} | Fecha: {req.fecha_soli}\n\n"

    if len(requisiciones) > 10:
        mensaje += f"... y {len(requisiciones) - 10} más\n\n"

    mensaje += "\nUsa `/ver <ID>` para ver detalles de una requisición."
    return mensaje
