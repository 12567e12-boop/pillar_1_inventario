from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='get_estado_badge')
def get_estado_badge(estado):
    """
    Returns a Bootstrap badge for the given estado
    """
    estado_classes = {
        'pendiente': 'bg-warning text-dark',
        'supervisor': 'bg-info text-dark',
        'autorizada': 'bg-primary',
        'rechazada': 'bg-danger',
        'surtida': 'bg-success',
        'cerrada': 'bg-secondary'
    }
    
    # Default class if estado not found
    badge_class = estado_classes.get(estado, 'bg-secondary')
    
    # Estado display text
    estado_display = dict(Requisicion.ESTADO_CHOICES).get(estado, estado)
    
    return mark_safe(f'<span class="badge {badge_class}">{estado_display}</span>')

# Import the Requisicion model at the bottom to avoid circular imports
from Almacen.models.requisiciones import Requisicion
