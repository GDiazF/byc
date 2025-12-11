# ============================================================================
# DECORADORES PARA VERIFICAR PERMISOS EN VISTAS BASADAS EN FUNCIONES
# ============================================================================
# Este modulo proporciona decoradores que se pueden usar en las vistas
# para verificar que el usuario tenga los permisos necesarios antes de
# ejecutar la vista.
#
# Ejemplo de uso:
#     @login_required
#     @permission_required_custom('rrhh_personal.view_personal')
#     def lista_personal(request):
#         ...
# ============================================================================

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def permission_required_custom(permiso_codigo, raise_exception=True, is_ajax=False):
    """
    Decorador para verificar permisos personalizados en vistas basadas en funciones.
    
    Puede usarse para permisos de modelo (ej: 'app.view_model') o permisos de acción
    (ej: 'app.custom_action'). Si el usuario no tiene el permiso, redirige con mensaje
    o retorna JSON según el tipo de petición.
    
    Args:
        permiso_codigo (str): El código del permiso a verificar (ej: 'rrhh_personal.desactivar_personal').
        raise_exception (bool): Si es True, levanta PermissionDenied. Si es False, redirige a la página de login.
        is_ajax (bool): Si es True, retorna JsonResponse con error 403 para peticiones AJAX.
        
    Returns:
        function: Decorador que envuelve la vista.
        
    Ejemplo:
        @login_required
        @permission_required_custom('rrhh_personal.view_personal')
        def lista_personal(request):
            ...
            
        @login_required
        @permission_required_custom('rrhh_personal.change_personal', is_ajax=True)
        def toggle_personal(request):
            return JsonResponse({'status': 'success'})
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if is_ajax:
                    from django.http import JsonResponse
                    return JsonResponse({'status': 'error', 'message': 'Autenticacion requerida'}, status=401)
                # Redirigir a login si no esta autenticado
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            if not request.user.has_perm(permiso_codigo):
                if is_ajax:
                    from django.http import JsonResponse
                    return JsonResponse({
                        'status': 'error', 
                        'message': 'No tiene permiso para realizar esta accion'
                    }, status=403)
                # En lugar de lanzar PermissionDenied, redirigir con mensaje
                from django.shortcuts import redirect
                from django.contrib import messages
                messages.error(
                    request,
                    'No tiene permiso para acceder a esta seccion. Por favor, contacte al administrador si necesita acceso.'
                )
                # Redirigir a la pagina anterior (donde estaba el usuario)
                referer = request.META.get('HTTP_REFERER')
                if referer:
                    return redirect(referer)
                # Si no hay referer, redirigir al inicio
                return redirect('/home/')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permission_required_multiple(*permisos_codigos, require_all=True, is_ajax=False):
    """
    Decorador para verificar múltiples permisos en vistas basadas en funciones.
    
    Permite verificar que el usuario tenga uno o varios permisos. Útil cuando una
    vista requiere múltiples permisos o cuando se acepta cualquiera de varios permisos.
    
    Args:
        *permisos_codigos: Códigos de permisos a verificar.
        require_all (bool): Si True, requiere TODOS los permisos.
                          Si False, requiere AL MENOS UNO de los permisos.
                          Default: True.
        is_ajax (bool): Si es True, retorna JsonResponse con error 403 para peticiones AJAX.
                       Default: False.
        
    Returns:
        function: Decorador que envuelve la vista.
        
    Ejemplo:
        # Requiere AMBOS permisos
        @permission_required_multiple(
            'rrhh_personal.view_personal',
            'rrhh_personal.add_personal',
            require_all=True
        )
        def crear_personal(request):
            ...
            
        # Requiere AL MENOS UNO de los permisos (para AJAX)
        @permission_required_multiple(
            'rrhh_personal.desactivar_personal',
            'rrhh_personal.activar_personal',
            require_all=False,
            is_ajax=True
        )
        def toggle_personal(request):
            return JsonResponse({'status': 'success'})
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if is_ajax:
                    from django.http import JsonResponse
                    return JsonResponse({'status': 'error', 'message': 'Autenticacion requerida'}, status=401)
                # Redirigir a login si no esta autenticado
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            if require_all:
                # Requiere TODOS los permisos
                tiene_todos = all(request.user.has_perm(perm) for perm in permisos_codigos)
                if not tiene_todos:
                    permisos_str = ', '.join(permisos_codigos)
                    if is_ajax:
                        from django.http import JsonResponse
                        return JsonResponse({
                            'status': 'error',
                            'message': f'No tiene todos los permisos necesarios. Se requieren: {permisos_str}'
                        }, status=403)
                    raise PermissionDenied(
                        f"No tienes todos los permisos necesarios. "
                        f"Se requieren: {permisos_str}"
                    )
            else:
                # Requiere AL MENOS UNO de los permisos
                tiene_alguno = any(request.user.has_perm(perm) for perm in permisos_codigos)
                if not tiene_alguno:
                    permisos_str = ' o '.join(permisos_codigos)
                    if is_ajax:
                        from django.http import JsonResponse
                        return JsonResponse({
                            'status': 'error',
                            'message': f'No tiene permiso para realizar esta accion. Se requiere al menos uno de: {permisos_str}'
                        }, status=403)
                    raise PermissionDenied(
                        f"No tienes ninguno de los permisos necesarios. "
                        f"Se requiere al menos uno de: {permisos_str}"
                    )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


