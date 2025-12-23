from django.urls import path
from . import views_requisiciones

app_name = 'requisiciones'

urlpatterns = [
    # Lista de requisiciones
    path('', views_requisiciones.lista_requisiciones, name='lista_requisiciones'),
    
    # Crear nueva requisición
    path('nueva/', views_requisiciones.crear_requisicion, name='crear_requisicion'),
    
    # Detalle de requisición
    path('<uuid:token_publico>/', views_requisiciones.detalle_requisicion, name='detalle_requisicion'),
    
    # Acciones sobre requisición
    path('<uuid:token_publico>/aprobar-supervisor/', 
         views_requisiciones.aprobar_requisicion_supervisor, 
         name='aprobar_requisicion_supervisor'),
    
    path('<uuid:token_publico>/aprobar-directivo/', 
         views_requisiciones.aprobar_requisicion_directivo, 
         name='aprobar_requisicion_directivo'),
    
    path('<uuid:token_publico>/rechazar/', 
         views_requisiciones.rechazar_requisicion, 
         name='rechazar_requisicion'),
    
    # API endpoints
    path('api/productos-por-especialidad/', 
         views_requisiciones.api_productos_por_especialidad, 
         name='api_productos_por_especialidad'),
]
