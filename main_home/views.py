from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
# Create your views here.

class HomeView(TemplateView, LoginRequiredMixin):
    template_name = 'home/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Preparar contexto para el dashboard
        # En el futuro, aquí se determinará qué dashboard mostrar según el rol del usuario
        context['mostrar_dashboard'] = True
        # TODO: Implementar lógica de roles
        # if self.request.user.has_perm('dashboards.view_rrhh'):
        #     context['dashboard_tipo'] = 'rrhh'
        # elif self.request.user.has_perm('dashboards.view_operaciones'):
        #     context['dashboard_tipo'] = 'operaciones'
        # etc.
        return context