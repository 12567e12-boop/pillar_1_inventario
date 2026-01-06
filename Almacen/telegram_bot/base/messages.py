"""
Templates de mensajes para el bot de Telegram.
"""
from datetime import date
from asgiref.sync import sync_to_async
from ..utils import escape_markdown


class Messages:
    """Clase con todos los mensajes del bot."""
    
    # Mensajes de bienvenida
    WELCOME = """Bienvenido al Bot de Requisiciones

Soy tu asistente para gestionar requisiciones de materiales.

En que puedo ayudarte?"""
    
    @staticmethod
    async def get_help_message(update=None):
        """
        Genera el mensaje de ayuda con el ID de Telegram del usuario.
        
        Args:
            update: Objeto Update de python-telegram-bot (opcional)
        """
        user_id = ""
        if update and update.effective_user:
            user_id = f"\n\n🔐 *Tu ID de Telegram:*\n`{update.effective_user.id}`\n\n"
            user_id += "📝 *Nota:* Comparte este ID con el administrador para vincular tu cuenta."

        return f"""
📚 *Ayuda - Bot de Requisiciones*

*Comandos para usuarios:*
• `/nueva` - Iniciar una nueva requisición
• `/mis_requisiciones` - Ver todas tus requisiciones
• `/ver <ID>` - Ver detalles de una requisición específica

*Comandos para supervisores/directivos:*
• `/aprobar <ID>` - Aprobar una requisición
• `/rechazar <ID>` - Rechazar una requisición

*Ejemplos:*
• `/ver REQ-001-2024`
• `/aprobar REQ-001-2024`

*Estados de requisiciones:*
🟡 Pendiente - Esperando aprobación del supervisor
🟠 Supervisor - Aprobada por supervisor, esperando directivo
🟢 Autorizada - Aprobada por ambos, lista para surtir
🔵 Surtida - Materiales entregados
⚫ Cerrada - Requisición finalizada
🔴 Rechazada - Requisición rechazada
{user_id}

¿Necesitas más ayuda? Contacta al administrador.
"""
    
    # Mensajes de requisiciones
    NUEVA_REQUISICION_INICIO = """
📝 *Nueva Requisición*

Vamos a crear una nueva requisición paso a paso.

*Paso 1:* Selecciona el bloque donde se realizará la obra:
"""

    NUEVA_REQUISICION_UBICACION = """
📝 *Nueva Requisición*

*Paso 2:* Ingresa la ubicación:
"""

    NUEVA_REQUISICION_OBRA = """
📝 *Nueva Requisición*

*Paso 3:* Ingresa el nombre de la obra:
"""

    NUEVA_REQUISICION_SUPERVISOR = """
📝 *Nueva Requisición*

*Paso 4:* Selecciona el supervisor:
"""

    NUEVA_REQUISICION_FECHA_UTIL = """
📝 *Nueva Requisición*

*Paso 5:* Ingresa la fecha a utilizar

*Hoy es:* {fecha_actual}

⚠️ *Restricciones:*
• La fecha debe ser igual o posterior a hoy
• No puedes seleccionar más de 2 semanas a futuro

*Formato:* DD/MM/YYYY
"""

    @staticmethod
    def obtener_mensaje_fecha_util() -> str:
        """
        Genera el mensaje del paso 5 con la fecha actual dinámicamente.
        
        Returns:
            str: Mensaje formateado con la fecha actual
        """
        from datetime import date
        fecha_hoy = date.today().strftime("%d/%m/%Y")
        return Messages.NUEVA_REQUISICION_FECHA_UTIL.format(fecha_actual=fecha_hoy)

    NUEVA_REQUISICION_ESPECIALIDAD = """
📝 *Nueva Requisición*

*Paso 6:* Selecciona la especialidad:
"""

    NUEVA_REQUISICION_IMAGEN = """
📝 *Nueva Requisición*

*Paso 7:* Adjunta una imagen de la requisición (obligatoria):

Toma una foto o sube una imagen de la requisición/materiales requeridos.
"""
    
    REQUISICION_CREADA = """
✅ *Requisición Creada*

Tu requisición ha sido creada exitosamente.

*ID:* {id}
*Solicitante:* {solicitante}
*Ubicación:* {ubicacion}
*Obra:* {obra}
*Supervisor:* {supervisor}
*Fecha a utilizar:* {fecha_util}
*Especialidad:* {especialidad}
*Estado:* 🟡 Pendiente

La requisición será revisada por el supervisor.
"""
    
    REQUISICION_NO_ENCONTRADA = """
❌ *Requisición no encontrada*

No se encontró ninguna requisición con el ID: `{id}`

Verifica el ID e intenta nuevamente.
"""
    
    # Mensajes de aprobación
    APROBACION_SUPERVISOR = """
✅ *Aprobación de Supervisor*

La requisición ha sido aprobada por el supervisor.

*ID:* {id}
*Estado:* 🟠 Esperando aprobación del directivo

Ahora debe ser revisada por el directivo.
"""
    
    APROBACION_DIRECTIVO = """
✅ *Aprobación de Directivo*

La requisición ha sido aprobada completamente.

*ID:* {id}
*Estado:* 🟢 Autorizada
*Folio:* {folio}

Los materiales han sido descontados del inventario.
La requisición está lista para ser surtida.
"""
    
    REQUISICION_RECHAZADA = """
❌ *Requisición Rechazada*

La requisición ha sido rechazada.

*ID:* {id}
*Motivo:* {motivo}
*Estado:* 🔴 Rechazada
"""
    
    # Mensajes de error
    ERROR_PERMISOS = """
⛔ *Sin permisos*

No tienes permisos para realizar esta acción.

Contacta al administrador si crees que esto es un error.
"""
    
    ERROR_ESTADO_INVALIDO = """
⚠️ *Estado inválido*

No se puede realizar esta acción en el estado actual de la requisición.

*Estado actual:* {estado}
*Acción solicitada:* {accion}
"""
    
    ERROR_GENERICO = """
❌ *Error*

Ocurrió un error al procesar tu solicitud:
{error}

Por favor, intenta nuevamente o contacta al administrador.
"""
    
    # Mensajes de confirmación
    CONFIRMAR_APROBACION = """
⚠️ *Confirmar Aprobación*

¿Estás seguro de aprobar esta requisición?

*ID:* {id}
*Obra:* {obra}
*Solicitante:* {solicitante}
*Artículos:* {num_articulos}

Esta acción no se puede deshacer.
"""
    
    CONFIRMAR_RECHAZO = """
⚠️ *Confirmar Rechazo*

¿Estás seguro de rechazar esta requisición?

*ID:* {id}
*Obra:* {obra}

Por favor, indica el motivo del rechazo:
"""
    
    @staticmethod
    def formato_requisicion(req) -> str:
        """
        Formatea una requisición para mostrar en Telegram.

        Args:
            req: Objeto Requisicion

        Returns:
            str: Mensaje formateado
        """
        # Emoji según estado
        estado_emoji = {
            'pendiente': '🟡',
            'supervisor': '🟠',
            'autorizada': '🟢',
            'surtida': '🔵',
            'cerrada': '⚫',
            'rechazada': '🔴',
        }

        emoji = estado_emoji.get(req.estado, '⚪')

        mensaje = f"""
📋 *Requisición {escape_markdown(req.id or 'SIN-ID')}*

{emoji} *Estado:* {escape_markdown(req.estado.upper())}

*Información General:*
→• Obra: {escape_markdown(req.obra)}
→• Solicitante: {escape_markdown(str(getattr(req, 'solicitante_nombre', None)) or (req.solicitante.nombre if req.solicitante else 'N/A'))}
→• Especialidad: {escape_markdown(req.especialidad)}
→• Bloque: {escape_markdown(req.bloque.nombre if req.bloque else 'N/A')}

*Solicitante:*
• Nombre: {escape_markdown(req.solicitante.nombre if req.solicitante else 'N/A')}

*Fechas:*
• Solicitud: {req.fecha_soli}
• Utilización: {req.fecha_util or 'N/A'}
• Surtido: {req.fecha_surt or 'N/A'}

*Autorizaciones:*
• Supervisor: {'✅' if req.autorizado_supervisor else '❌'}
• Directivo: {'✅' if req.autorizado_directivo else '❌'}

*Artículos:* {req.numero_de_articulos}

*Observaciones:*
{escape_markdown(req.observaciones or 'Sin observaciones')}
"""
        return mensaje
    
    @staticmethod
    @sync_to_async
    def lista_requisiciones(requisiciones) -> str:
        """
        Formatea una lista de requisiciones pendientes (global).

        Args:
            requisiciones: Lista de requisiciones pendientes

        Returns:
            str: Mensaje formateado
        """
        if not requisiciones:
            return "📭 No hay requisiciones pendientes en este momento."

        mensaje = "📋 *Requisiciones Pendientes:*\n\n"

        for req in requisiciones:
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
            mensaje += f"   Solicitante: {escape_markdown(req.solicitante.nombre if req.solicitante else 'N/A')}\n"
            mensaje += f"   Fecha: {req.fecha_soli}\n\n"

        mensaje += "\nUsa `/ver <ID>` para ver detalles de una requisición."
        return mensaje
    
    @staticmethod
    def formato_detalles(detalles) -> str:
        """
        Formatea los detalles de una requisición.

        Args:
            detalles: QuerySet de DetalleRequisicion

        Returns:
            str: Mensaje formateado
        """
        if not detalles:
            return "Sin artículos registrados."

        mensaje = "*Artículos solicitados:*\n\n"

        for i, det in enumerate(detalles, 1):
            mensaje += f"{i}. {escape_markdown(det.producto.nombre)}\n"
            mensaje += f"   • Cantidad: {det.cantidad} {escape_markdown(det.unidad.nombre if hasattr(det.unidad, 'nombre') else str(det.unidad))}\n"
            if det.comentario:
                mensaje += f"   • Comentario: {escape_markdown(det.comentario)}\n"
            mensaje += "\n"

        return mensaje
