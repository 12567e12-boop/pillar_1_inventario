"""
Servicios específicos para la gestión de requisiciones en el bot de Telegram.

Este módulo contiene la lógica de negocio relacionada con requisiciones,
separada de los servicios generales para mantener la modularidad.
"""
import logging
from typing import Optional, List, Dict, Any
from django.contrib.auth.models import User
from django.db.models import Q
from asgiref.sync import sync_to_async
import os
from Almacen.models.requisiciones.requisiciones import Requisicion
from Almacen.models.requisiciones.detalles import DetalleRequisicion
from Almacen.models.base.base import Bloque, Producto, Unidad
from Almacen.models.personal.personal import Empleado

logger = logging.getLogger(__name__)


class RequisicionService:
    """
    Servicio para gestionar requisiciones a través del bot.

    Proporciona métodos para crear, listar, aprobar y gestionar
    el ciclo de vida de las requisiciones desde Telegram.
    """

    @staticmethod
    async def crear_requisicion(
        obra: str,
        ubicacion: str,
        especialidad: str,
        supervisor_id: int,  # Changed from supervisor name to supervisor_id
        fecha_util: str,
        solicitante_nombre: str,
        bloque_id: Optional[int] = None,
        solicitante_id: Optional[int] = None,
        usuario: Optional[User] = None,
        telegram_user=None,
        imagen: Optional[str] = None
    ) -> Requisicion:
        """
        Crea una nueva requisición desde el bot.

        Args:
            obra: Nombre de la obra
            ubicacion: Ubicación de la obra
            especialidad: Especialidad requerida
            supervisor_id: ID del empleado supervisor
            fecha_util: Fecha de utilización en formato DD/MM/YYYY
            solicitante_nombre: Nombre del solicitante
            bloque_id: ID del bloque (opcional)
            solicitante_id: ID del empleado solicitante (opcional)
            usuario: Usuario que crea la requisición (opcional)
            telegram_user: Usuario de Telegram (opcional)
            imagen: Imagen adjunta (opcional)

        Returns:
            Requisicion: La requisición creada

        Raises:
            Exception: Si ocurre un error durante la creación
        """
        from asgiref.sync import sync_to_async
        from django.db import transaction
        from ..models import Bloque, Empleado, Requisicion
        from telegram import Bot
        from telegram.helpers import escape_markdown

        @sync_to_async
        def _crear_requisicion_sync():
            with transaction.atomic():
                try:
                    from datetime import datetime

                    bloque = None
                    if bloque_id:
                        bloque = Bloque.objects.get(id=bloque_id)

                    solicitante = None
                    if solicitante_id:
                        solicitante = Empleado.objects.get(id=solicitante_id)

                    # Convertir fecha_util de string a date
                    fecha_util_date = None
                    if fecha_util:
                        try:
                            fecha_util_date = datetime.strptime(fecha_util, '%d/%m/%Y').date()
                        except ValueError:
                            raise ValueError("Formato de fecha inválido. Use DD/MM/YYYY")

                    # Crear la requisición
                    requisicion = Requisicion(
                        obra=obra,
                        ubicacion=ubicacion,
                        especialidad=especialidad,
                        bloque=bloque,
                        solicitante=solicitante,
                        solicitante_nombre=solicitante_nombre,
                        fecha_util=fecha_util_date,
                        usuario_creador=usuario
                    )
                    
                    # Asignar la imagen si se proporciona
                    if imagen is not None:
                        # Asegurarse de que la ruta sea relativa al directorio de medios
                        if not str(imagen).startswith('requisiciones/'):
                            imagen_path = f'requisiciones/{os.path.basename(str(imagen))}'
                        else:
                            imagen_path = str(imagen)
                        requisicion.imagen = imagen_path
                        logger.info(f"Imagen asignada a la requisición: {requisicion.imagen}")

                    # Asignar el supervisor
                    try:
                        supervisor_obj = Empleado.objects.get(id=supervisor_id)
                        requisicion.supervisor = supervisor_obj
                        logger.info(f"Supervisor {supervisor_obj.nombre} asignado a la requisición")
                    except Empleado.DoesNotExist:
                        logger.warning(f"No se encontró el supervisor con ID {supervisor_id}")
                        # Mantener el supervisor en observaciones por compatibilidad
                        requisicion.observaciones = f"Supervisor ID: {supervisor_id}"

                    requisicion.generar_id()
                    requisicion.save()

                    logger.info(f"Requisición creada desde bot: {requisicion.id}")
                    return requisicion

                except Exception as e:
                    logger.error(f"Error al crear requisición desde bot: {e}")
                    raise

        # Llamar a la función síncrona
        requisicion = await _crear_requisicion_sync()
        
        # Notificar al supervisor si tiene ID de Telegram
        try:
            # Intentar obtener el supervisor
            @sync_to_async
            def _get_supervisor():
                try:
                    supervisor_obj = Empleado.objects.get(id=supervisor_id)
                    return supervisor_obj
                except Empleado.DoesNotExist:
                    logger.warning(f"No se encontró el supervisor con ID {supervisor_id}")
                    return None
                except Exception as e:
                    logger.error(f"Error al buscar supervisor: {e}")
                    return None

            supervisor_obj = await _get_supervisor()
            
            if supervisor_obj and supervisor_obj.telegram_id:
                from django.conf import settings
                from telegram import Bot
                
                # Crear mensaje para el supervisor
                mensaje_supervisor = (
                    f"📋 *Nueva Requisición Pendiente*\n\n"
                    f"*Obra:* {requisicion.obra}\n"
                    f"*Ubicación:* {requisicion.ubicacion}\n"
                    f"*Solicitante:* {requisicion.solicitante_nombre}\n"
                    f"*Fecha requerida:* {requisicion.fecha_util.strftime('%d/%m/%Y')}\n\n"
                    "Por favor revisa la aplicación para aprobarla o rechazarla."
                )
                
                try:
                    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
                    await bot.send_message(
                        chat_id=supervisor_obj.telegram_id,
                        text=mensaje_supervisor,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Error al enviar notificación al supervisor: {e}")
            
        except Exception as e:
            logger.error(f"Error en el proceso de notificación: {e}")

        return requisicion

    @staticmethod
    @sync_to_async
    def obtener_requisicion(req_id: str) -> Optional[Requisicion]:
        """
        Obtiene una requisición por su ID para el bot.

        Args:
            req_id: ID de la requisición

        Returns:
            Requisicion o None si no existe
        """
        try:
            return Requisicion.objects.get(id=req_id)
        except Requisicion.DoesNotExist:
            logger.warning(f"Requisición no encontrada desde bot: {req_id}")
            return None

    @staticmethod
    def obtener_requisicion_por_token(token: str) -> Optional[Requisicion]:
        """
        Obtiene una requisición por su token público desde el bot.

        Args:
            token: Token público UUID

        Returns:
            Requisicion o None si no existe
        """
        try:
            return Requisicion.objects.get(token_publico=token)
        except Requisicion.DoesNotExist:
            logger.warning(f"Requisición no encontrada con token desde bot: {token}")
            return None

    @staticmethod
    async def actualizar_imagen(
        token_publico,
        imagen_path: str,
        telegram_user=None,
    ) -> Optional[Requisicion]:
        """Actualiza la imagen de una requisición identificada por su token público.

        Args:
            token_publico: Token público UUID de la requisición
            imagen_path: Ruta relativa dentro de media (por ejemplo 'requisiciones/archivo.jpg')
            telegram_user: Usuario de Telegram que envía la imagen (opcional, solo para logging)

        Returns:
            La requisición actualizada o None si no se encontró.
        """
        from asgiref.sync import sync_to_async

        @sync_to_async
        def _update():
            try:
                req = Requisicion.objects.get(token_publico=token_publico)

                # Normalizar la ruta para que siempre quede bajo 'requisiciones/'
                if not str(imagen_path).startswith('requisiciones/'):
                    imagen_rel = os.path.join('requisiciones', os.path.basename(str(imagen_path)))
                else:
                    imagen_rel = str(imagen_path)

                req.imagen = imagen_rel
                req.save(update_fields=['imagen'])

                logger.info(
                    "Imagen actualizada para requisición %s (token %s) por usuario Telegram %s",
                    getattr(req, 'id', None),
                    token_publico,
                    getattr(telegram_user, 'telegram_id', None) if telegram_user else None,
                )
                return req
            except Requisicion.DoesNotExist:
                logger.warning(
                    "No se encontró la requisición con token %s al intentar actualizar imagen",
                    token_publico,
                )
                return None
            except Exception as e:
                logger.error(f"Error al actualizar imagen de requisición: {e}")
                raise

        return await _update()

    @staticmethod
    @sync_to_async
    def listar_requisiciones(
        usuario: User = None,
        estado: str = None,
        desde_fecha: str = None,
        solicitante_id: int = None,
        supervisor_id: int = None,
        excluir_estados: list = None
    ) -> List[Requisicion]:
        """
        Lista TODAS las requisiciones sin filtrar por estado ni fecha.
        
        Args:
            Los parámetros se mantienen por compatibilidad pero no se usan
            
        Returns:
            Lista de todas las requisiciones ordenadas por fecha descendente
        """
        # Obtener todas las requisiciones sin filtrar por fecha
        queryset = Requisicion.objects.all().order_by('-fecha_soli')
        
        # Convertir a lista y devolver
        return list(queryset)

    @staticmethod
    def aprobar_supervisor(req_id: str, supervisor=None, usuario: Optional[User] = None) -> Dict[str, Any]:
        """
        Aprueba una requisición como supervisor desde el bot.

        Args:
            req_id: ID de la requisición
            supervisor: Objeto Empleado del supervisor que aprueba
            usuario: Usuario que aprueba (opcional)

        Returns:
            Dict con resultado de la operación
        """
        try:
            requisicion = Requisicion.objects.get(id=req_id)

            if requisicion.estado != "pendiente":
                return {
                    "success": False,
                    "error": f"La requisición está en estado '{requisicion.estado}', no se puede aprobar."
                }

            # Verificar que el supervisor que aprueba sea el asignado
            if supervisor and requisicion.supervisor and requisicion.supervisor.id != supervisor.id:
                return {
                    "success": False,
                    "error": "No tienes permiso para aprobar esta requisición."
                }

            requisicion.aprobar_supervisor(supervisor=supervisor, usuario=usuario)

            logger.info(f"Requisición {req_id} aprobada por supervisor {supervisor.id if supervisor else 'desconocido'} desde bot")
            return {
                "success": True,
                "requisicion": requisicion,
                "mensaje": "Requisición aprobada por supervisor"
            }

        except Requisicion.DoesNotExist:
            return {"success": False, "error": "Requisición no encontrada"}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error al aprobar requisición desde bot: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    @sync_to_async
    def aprobar_directivo(req_id: str, usuario: Optional[User] = None) -> Dict[str, Any]:
        """
        Aprueba una requisición como directivo desde el bot.

        Args:
            req_id: ID de la requisición
            usuario: Usuario que aprueba

        Returns:
            Dict con resultado de la operación
        """
        try:
            requisicion = Requisicion.objects.get(id=req_id)

            if requisicion.estado != "supervisor":
                return {
                    "success": False,
                    "error": f"La requisición está en estado '{requisicion.estado}', debe estar en 'supervisor'."
                }

            if not requisicion.autorizado_supervisor:
                return {
                    "success": False,
                    "error": "El supervisor debe aprobar primero."
                }

            # Asegurarse de que tenemos un objeto de usuario válido
            if usuario and hasattr(usuario, '_wrapped') and hasattr(usuario, '_setup'):
                if not usuario._wrapped:
                    usuario._setup()
                usuario = usuario._wrapped

            # Llamar al método del modelo
            requisicion.aprobar_directivo(usuario=usuario)

            logger.info(f"Requisición {req_id} aprobada por directivo desde bot")
            return {
                "success": True,
                "requisicion": requisicion,
                "mensaje": "Requisición aprobada por directivo",
                "folio": requisicion.id
            }

        except Requisicion.DoesNotExist:
            return {"success": False, "error": "Requisición no encontrada"}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error al aprobar requisición desde bot: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @staticmethod
    @sync_to_async
    def rechazar(req_id: str, motivo: str, usuario: Optional[User] = None) -> Dict[str, Any]:
        """
        Rechaza una requisición desde el bot.

        Args:
            req_id: ID de la requisición
            motivo: Motivo del rechazo
            usuario: Usuario que rechaza (no utilizado en el modelo actual)

        Returns:
            Dict con resultado de la operación
        """
        from django.core.exceptions import ObjectDoesNotExist
        
        try:
            requisicion = Requisicion.objects.get(id=req_id)

            if requisicion.estado in ["cerrada", "rechazada"]:
                return {
                    "success": False,
                    "error": f"La requisición ya está {requisicion.estado}."
                }

            # Llamar al método rechazar del modelo
            requisicion.rechazar(motivo=motivo)

            logger.info(f"Requisición {req_id} rechazada desde bot")
            return {
                "success": True,
                "requisicion": requisicion,
                "mensaje": "Requisición rechazada"
            }

        except ObjectDoesNotExist:
            return {"success": False, "error": "Requisición no encontrada"}
        except Exception as e:
            logger.error(f"Error al rechazar requisición desde bot: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def marcar_surtida(req_id: str, usuario: Optional[User] = None) -> Dict[str, Any]:
        """
        Marca una requisición como surtida desde el bot.

        Args:
            req_id: ID de la requisición
            usuario: Usuario que marca como surtida

        Returns:
            Dict con resultado de la operación
        """
        try:
            requisicion = Requisicion.objects.get(id=req_id)

            if requisicion.estado != "autorizada":
                return {
                    "success": False,
                    "error": "Solo se puede marcar como surtida si está autorizada."
                }

            requisicion.marcar_surtida(usuario=usuario)

            logger.info(f"Requisición {req_id} marcada como surtida desde bot")
            return {
                "success": True,
                "requisicion": requisicion,
                "mensaje": "Requisición marcada como surtida"
            }

        except Requisicion.DoesNotExist:
            return {"success": False, "error": "Requisición no encontrada"}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error al marcar como surtida desde bot: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def cerrar(req_id: str, usuario: Optional[User] = None) -> Dict[str, Any]:
        """
        Cierra una requisición desde el bot.

        Args:
            req_id: ID de la requisición
            usuario: Usuario que cierra

        Returns:
            Dict con resultado de la operación
        """
        try:
            requisicion = Requisicion.objects.get(id=req_id)

            if requisicion.estado != "surtida":
                return {
                    "success": False,
                    "error": "Solo se puede cerrar si está surtida."
                }

            requisicion.cerrar(usuario=usuario)

            logger.info(f"Requisición {req_id} cerrada desde bot")
            return {
                "success": True,
                "requisicion": requisicion,
                "mensaje": "Requisición cerrada"
            }

        except Requisicion.DoesNotExist:
            return {"success": False, "error": "Requisición no encontrada"}
        except Exception as e:
            logger.error(f"Error al cerrar requisición desde bot: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def agregar_detalle(
        req_id: str,
        producto_id: int,
        cantidad: float,
        unidad_id: int,
        comentario: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Agrega un detalle (artículo) a una requisición desde el bot.

        Args:
            req_id: ID de la requisición
            producto_id: ID del producto
            cantidad: Cantidad solicitada
            unidad_id: ID de la unidad
            comentario: Comentario opcional

        Returns:
            Dict con resultado de la operación
        """
        try:
            requisicion = Requisicion.objects.get(id=req_id)
            producto = Producto.objects.get(id=producto_id)
            unidad = Unidad.objects.get(id=unidad_id)

            detalle = DetalleRequisicion.objects.create(
                requisicion=requisicion,
                producto=producto,
                unidad=unidad,
                cantidad=cantidad,
                comentario=comentario
            )

            # Actualizar contador de artículos
            requisicion.numero_de_articulos = requisicion.detallerequisicion_set.count()
            requisicion.save(update_fields=['numero_de_articulos'])

            logger.info(f"Detalle agregado a requisición {req_id} desde bot")
            return {
                "success": True,
                "detalle": detalle,
                "mensaje": "Artículo agregado correctamente"
            }

        except (Requisicion.DoesNotExist, Producto.DoesNotExist, Unidad.DoesNotExist) as e:
            return {"success": False, "error": f"No encontrado: {e}"}
        except Exception as e:
            logger.error(f"Error al agregar detalle desde bot: {e}")
            return {"success": False, "error": str(e)}


class CatalogoService:
    """
    Servicio para gestionar catálogos relacionados con requisiciones.

    Proporciona acceso a bloques, empleados, productos y unidades
    para el funcionamiento del bot.
    """

    @staticmethod
    @sync_to_async
    def listar_bloques() -> List[Bloque]:
        """
        Lista todos los bloques disponibles para requisiciones.

        Returns:
            Lista de bloques ordenados por nombre
        """
        return list(Bloque.objects.all().order_by('nombre'))
    
    @staticmethod
    @sync_to_async
    def obtener_bloques() -> List[Bloque]:
        """
        Obtiene todos los bloques disponibles (alias de listar_bloques).

        Returns:
            Lista de bloques ordenados por nombre
        """
        return list(Bloque.objects.all().order_by('nombre'))

    @staticmethod
    @sync_to_async
    def listar_empleados(busqueda: Optional[str] = None) -> List[Empleado]:
        """
        Lista empleados con búsqueda opcional para el bot.

        Args:
            busqueda: Término de búsqueda (nombre o puesto)

        Returns:
            Lista de empleados ordenados por nombre (limitada a 20)
        """
        queryset = Empleado.objects.all()

        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda) |
                Q(puesto__icontains=busqueda)
            )

        return queryset.order_by('nombre')[:20]
    
    @staticmethod
    @sync_to_async
    def listar_supervisores() -> List[Empleado]:
        """
        Lista todos los supervisores disponibles para requisiciones.

        Returns:
            Lista de empleados con rol supervisor ordenados por nombre
        """
        return list(Empleado.objects.filter(rol='supervisor').order_by('nombre'))

    @staticmethod
    @sync_to_async
    def listar_productos(busqueda: Optional[str] = None) -> List[Producto]:
        """
        Lista productos con búsqueda opcional para el bot.

        Args:
            busqueda: Término de búsqueda (nombre)

        Returns:
            Lista de productos ordenados por nombre (limitada a 20)
        """
        queryset = Producto.objects.all()

        if busqueda:
            queryset = queryset.filter(nombre__icontains=busqueda)

        return queryset.order_by('nombre')[:20]

    @staticmethod
    @sync_to_async
    def listar_unidades() -> List[Unidad]:
        """
        Lista todas las unidades disponibles para el bot.

        Returns:
            Lista de unidades ordenadas por nombre
        """
        return list(Unidad.objects.all().order_by('nombre'))

    @staticmethod
    @sync_to_async
    def buscar_producto(nombre: str) -> Optional[Producto]:
        """
        Busca un producto por nombre exacto para el bot.

        Args:
            nombre: Nombre del producto

        Returns:
            Producto o None si no existe
        """
        try:
            return Producto.objects.get(nombre__iexact=nombre)
        except Producto.DoesNotExist:
            return None
        except Producto.MultipleObjectsReturned:
            # Si hay múltiples, devolver el primero
            return Producto.objects.filter(nombre__iexact=nombre).first()
