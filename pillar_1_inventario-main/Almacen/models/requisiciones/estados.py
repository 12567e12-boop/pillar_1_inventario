"""
Funciones de utilidad para gestionar transiciones de estado en requisiciones.
"""
from django.utils import timezone


def aplicar_transicion(requisicion, nuevo_estado, usuario=None, motivo=None):
    """
    Aplica una transición de estado a una requisición.

    Args:
        requisicion: Instancia del modelo Requisicion
        nuevo_estado: Nuevo estado a aplicar
        usuario: Usuario que realiza la transición (opcional)
        motivo: Motivo adicional (para rechazos)

    Returns:
        None
    """
    # Validar transición
    estados_validos = ['pendiente', 'supervisor', 'autorizada', 'rechazada', 'surtida', 'cerrada']

    if nuevo_estado not in estados_validos:
        raise ValueError(f"Estado '{nuevo_estado}' no es válido")

    # Aplicar transición
    estado_anterior = requisicion.estado
    requisicion.estado = nuevo_estado

    # Agregar información adicional según el estado
    if nuevo_estado == 'rechazada' and motivo:
        requisicion.observaciones = motivo

    elif nuevo_estado == 'surtida':
        from datetime import date
        requisicion.fecha_surt = date.today()

    # Log de la transición (opcional)
    print(f"[TRANSICIÓN] {requisicion} | {estado_anterior} → {nuevo_estado}")

    # Aquí podrías agregar logging a una tabla de auditoría
    # TransicionRequisicion.objects.create(
    #     requisicion=requisicion,
    #     estado_anterior=estado_anterior,
    #     estado_nuevo=nuevo_estado,
    #     usuario=usuario,
    #     fecha=timezone.now()
    # )
