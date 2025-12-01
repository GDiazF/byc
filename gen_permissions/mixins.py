"""
Mixins para verificar permisos en vistas basadas en clases (Class-Based Views).

Este módulo proporciona mixins que se pueden usar en las vistas basadas en clases
para verificar que el usuario tenga los permisos necesarios antes de ejecutar la vista.

Ejemplo de uso:
    class ListaPersonalView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
        permission_required = 'rrhh_personal.view_personal'
        model = Personal
        ...
"""

from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin


class PermissionRequiredMixin(AccessMixin):
    """
    Mixin para verificar que el usuario tenga un permiso específico.
    
    Similar al PermissionRequiredMixin de Django, pero más flexible.
    Permite especificar un solo permiso o múltiples permisos.
    
    Atributos de clase:
        permission_required (str o list): Permiso(s) requerido(s).
                                         Formato: 'app_label.codename'
        permission_required_all (bool): Si True, requiere TODOS los permisos.
                                       Si False, requiere AL MENOS UNO.
                                       Solo aplica si permission_required es una lista.
                                       Default: True
    
    Ejemplo:
        class ListaPersonalView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
            permission_required = 'rrhh_personal.view_personal'
            model = Personal
            template_name = 'personal/lista.html'
        
        class CrearPersonalView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
            permission_required = ['rrhh_personal.view_personal', 'rrhh_personal.add_personal']
            permission_required_all = True  # Requiere ambos permisos
            model = Personal
            form_class = PersonalForm
    """
    # Permiso requerido (puede ser string o lista)
    permission_required = None
    # Si es lista, indica si requiere todos o al menos uno
    permission_required_all = True
    
    def dispatch(self, request, *args, **kwargs):
        """
        Método que se ejecuta antes de cualquier método HTTP (get, post, etc.).
        
        Verifica que el usuario tenga el permiso requerido antes de continuar.
        """
        # Verificar que se haya especificado un permiso
        if self.permission_required is None:
            raise ValueError(
                f"{self.__class__.__name__} requiere especificar 'permission_required'"
            )
        
        # Verificar permisos
        if isinstance(self.permission_required, str):
            # Un solo permiso
            if not request.user.has_perm(self.permission_required):
                return self.handle_no_permission()
        elif isinstance(self.permission_required, (list, tuple)):
            # Múltiples permisos
            if self.permission_required_all:
                # Requiere TODOS los permisos
                tiene_todos = all(request.user.has_perm(perm) for perm in self.permission_required)
                if not tiene_todos:
                    return self.handle_no_permission()
            else:
                # Requiere AL MENOS UNO de los permisos
                tiene_alguno = any(request.user.has_perm(perm) for perm in self.permission_required)
                if not tiene_alguno:
                    return self.handle_no_permission()
        else:
            raise ValueError(
                f"'permission_required' debe ser un string o una lista, "
                f"no {type(self.permission_required).__name__}"
            )
        
        # Si tiene los permisos, continuar normalmente
        return super().dispatch(request, *args, **kwargs)
    
    def handle_no_permission(self):
        """
        Método que se ejecuta cuando el usuario no tiene permiso.
        
        En lugar de lanzar PermissionDenied (403 Forbidden), redirige a la página anterior
        con un mensaje de error usando el sistema de mensajes de Django.
        """
        from django.shortcuts import redirect
        from django.contrib import messages
        
        # Mensaje amigable para el usuario
        messages.error(
            self.request,
            'No tiene permiso para acceder a esta sección. Por favor, contacte al administrador si necesita acceso.'
        )
        
        # Redirigir a la página anterior (donde estaba el usuario)
        referer = self.request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        # Si no hay referer, redirigir al inicio
        return redirect('/home/')

