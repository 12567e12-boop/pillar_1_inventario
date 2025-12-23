from django import template

register = template.Library()

@register.filter(name='get_estado_badge')
def get_estado_badge(estado):
    """
    Returns the appropriate Bootstrap badge class for a given status.
    """
    badge_classes = {
        'pendiente': 'warning',
        'supervisor': 'info',
        'autorizada': 'success',
        'rechazada': 'danger',
        'completada': 'success',
        'cancelada': 'secondary',
    }
    return badge_classes.get(estado, 'secondary')
