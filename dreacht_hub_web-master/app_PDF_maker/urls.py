from django.urls import path
from .views import views_requisicion as views_requisicion
from .views import views_requisicion as views_requisicion
from .views import views_gafete as views_gafete
from .views import views_api as views_api


urlpatterns = [
    path('', views_gafete.home, name='home'),
    path('recursos/', views_gafete.recursos, name='recursos'),
    path('requisiciones/', views_requisicion.requisiciones, name='requisiciones'),
    path('requisiciones/edit/<str:token>/', views_requisicion.requisiciones_edit, name='requisiciones_edit'),
    path('gafetes/', views_gafete.gafetes, name='gafetes'),
    path('api/productos/', views_api.get_productos_por_especialidad, name='api_productos')


]
