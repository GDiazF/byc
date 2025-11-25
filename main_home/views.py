from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.views.generic import TemplateView
from django.views import View
from django.contrib.auth.forms import PasswordChangeForm
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

@login_required
def perfil_view(request):
    """Vista para mostrar el perfil del usuario"""
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'home/perfil.html', context)

@login_required
def cambiar_contraseña_view(request):
    """Vista para cambiar la contraseña del usuario"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Importante: actualiza la sesión para evitar logout
            messages.success(request, 'Tu contraseña ha sido actualizada exitosamente.')
            return redirect('home:perfil')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'home/cambiar_contraseña.html', context)