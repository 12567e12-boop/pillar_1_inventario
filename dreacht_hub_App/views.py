from django.shortcuts import render
from django.views import View

class HomeView(View):
    template_name = 'dreacht_hub_App/home.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'title': 'Dreacht Hub - Inicio',
            'active_page': 'home'
        })

# Otras vistas pueden ir aquí
