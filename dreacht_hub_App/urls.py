from django.urls import path
from .views import HomeView

app_name = 'dreacht_hub_App'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    # Otras URLs pueden ir aquí
]
