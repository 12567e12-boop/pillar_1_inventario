from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from Almacen import views


urlpatterns = [
    path('', views.index, name="index"),

    path('pages/error403', views.error403, name="error403"),
    path('pages/error404', views.error404, name="error404"),
    path('pages/registros', views.registros, name="registros"),
    path('pages/transferencias', views.transferencias, name="transferencias"),
    path('pages/prestados', views.prestados, name="prestados"),
    path('pages/temporales', views.temporales, name="temporales"),
    path('pages/dashboard', views.dashboard, name="dashboard"),
    path('registro/add', views.registro_add, name="registro_add"),
    path('registro/devolver', views.registro_devolver, name="registro_devolver"),
    path('registro/refresh', views.registro_refresh, name="registro_refresh"),
    path('transferencia/retornar', views.transferencia_retornar, name="transferencia_retornar"),
    path('bloque/exists', views.bloque_exists, name="bloque_exists"),
    path('empleado/exists', views.empleado_exists, name="empleado_exists"),
    path('producto/transferir', views.producto_transferir, name="producto_transferir"),
    path('producto/exists', views.producto_exists, name="producto_exists"),
    path('unidad/exists', views.unidad_exists, name="unidad_exists"),
    path('inventario/refresh', views.inventario_refresh, name="inventario_refresh"),
    path('devueltos/refresh', views.devueltos_refresh, name="devueltos_refresh"),
    path('retornados/refresh', views.retornados_refresh, name="retornados_refresh"),
    path('gafete/<int:empleado_id>/', views.generar_gafete_pdf, name='gafete_pdf'),
    
    # Requisiciones
    path('requisiciones/', include('Almacen.urls_requisiciones')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
