# ============================================================================
# VISTAS PARA MAIN_HOME
# ============================================================================
# Este archivo contiene las vistas para la aplicación main_home:
# - HomeView: Vista principal de la aplicación (dashboard)
# - perfil_view: Vista para mostrar el perfil del usuario
# - cambiar_contraseña_view: Vista para cambiar la contraseña del usuario
# ============================================================================

from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.views.generic import TemplateView
from django.views import View
from .forms import PasswordChangeForm

class HomeView(TemplateView, LoginRequiredMixin):
    """
    Vista principal del dashboard de la aplicación.
    
    Renderiza la página de inicio del sistema después del login.
    En el futuro se determinará qué dashboard mostrar según el rol del usuario.
    """
    template_name = 'home/index.html'
    
    def get_context_data(self, **kwargs):
        """
        Prepara el contexto para el template del dashboard.
        
        Args:
            **kwargs: Argumentos adicionales del contexto.
            
        Returns:
            dict: Contexto con datos para renderizar el template.
        """
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
    """
    Vista para mostrar el perfil del usuario autenticado.
    
    Muestra la información del usuario actual incluyendo datos básicos,
    permisos y opciones de configuración.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP del usuario autenticado.
        
    Returns:
        HttpResponse: Renderiza el template 'home/perfil.html' con los datos del usuario.
    """
    user = request.user
    context = {
        'user': user,
    }
    return render(request, 'home/perfil.html', context)

@login_required
def cambiar_contraseña_view(request):
    """
    Vista para cambiar la contraseña del usuario autenticado.
    
    Permite al usuario cambiar su contraseña mediante un formulario.
    Después de cambiar la contraseña exitosamente, crea una notificación
    de seguridad y actualiza la sesión para evitar logout automático.
    
    Args:
        request (HttpRequest): Objeto de solicitud HTTP del usuario autenticado.
                              Método POST para procesar el cambio, GET para mostrar el formulario.
        
    Returns:
        HttpResponse: 
            - Si es POST y válido: Redirige al perfil con mensaje de éxito.
            - Si es POST e inválido: Renderiza el formulario con errores.
            - Si es GET: Renderiza el formulario vacío.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Importante: actualiza la sesión para evitar logout
            
            # Crear notificación de cambio de contraseña
            try:
                from notificaciones.utils import crear_notificacion_para_usuario
                from django.utils import timezone
                
                fecha_cambio = timezone.now().strftime('%d/%m/%Y %H:%M')
                crear_notificacion_para_usuario(
                    usuario=user,
                    codigo_tipo='GENERAL_CAMBIO_PASSWORD',
                    titulo='Contraseña cambiada',
                    mensaje=f'Tu contraseña ha sido cambiada el {fecha_cambio}. Si no fuiste tú, contacta al administrador.',
                    datos_adicionales={
                        'fecha_cambio': timezone.now().isoformat(),
                        'ip_address': request.META.get('REMOTE_ADDR', ''),
                        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
                    },
                    prioridad='MEDIA'
                )
            except Exception as e:
                # Si falla la notificación, no fallar el cambio de contraseña
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al crear notificación de cambio de contraseña: {str(e)}")
            
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
