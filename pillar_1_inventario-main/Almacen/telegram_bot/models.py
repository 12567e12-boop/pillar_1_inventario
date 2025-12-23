"""
Módulo de modelos para el bot de Telegram.

Este módulo reexporta los modelos necesarios para el funcionamiento del bot,
proporcionando una interfaz unificada para el resto del código.
"""
# Re-exportar modelos de requisiciones
from Almacen.models.requisiciones.requisiciones import Requisicion
from Almacen.models.requisiciones.detalles import DetalleRequisicion
from Almacen.models.base.base import Bloque, Producto, Unidad
from Almacen.models.personal.personal import Empleado
from Almacen.models.telegram_user import TelegramUser

__all__ = [
    'Requisicion',
    'DetalleRequisicion',
    'Bloque',
    'Producto',
    'Unidad',
    'Empleado',
    'TelegramUser',
]
