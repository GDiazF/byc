# ============================================================================
# MIDDLEWARE PARA MANEJAR ERRORES DE PERMISOS DE MANERA AMIGABLE
# ============================================================================
# Este middleware intercepta errores 403 (PermissionDenied) y los convierte
# en respuestas JSON amigables para peticiones AJAX, permitiendo que el
# frontend muestre mensajes de error apropiados.
# ============================================================================

from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
import json


class PermissionDeniedMiddleware:
    """
    Middleware que convierte errores PermissionDenied en respuestas JSON para peticiones AJAX.
    
    Si la petición es AJAX y se lanza PermissionDenied, retorna un JSON con un mensaje
    amigable en lugar de un error 403 HTML. Esto permite que el frontend maneje los
    errores de permisos de forma más elegante.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Procesa excepciones y convierte PermissionDenied en JSON para AJAX.
        
        Si la excepción es PermissionDenied y la petición es AJAX, retorna una
        respuesta JSON con un mensaje amigable en lugar de dejar que Django maneje
        el error 403 normalmente.
        
        Args:
            request: Objeto HttpRequest.
            exception: Excepción lanzada.
            
        Returns:
            JsonResponse|None: Respuesta JSON si es PermissionDenied y AJAX,
                              None en caso contrario para que Django maneje el error.
        """
        if isinstance(exception, PermissionDenied):
            # Verificar si es una peticion AJAX
            is_ajax = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                request.content_type == 'application/json' or
                request.GET.get('format') == 'json' or
                request.POST.get('format') == 'json' or
                'application/json' in request.META.get('HTTP_ACCEPT', '')
            )
            
            if is_ajax:
                # Retornar JSON con mensaje amigable
                return JsonResponse({
                    'status': 'error',
                    'message': 'No tiene permiso para realizar esta accion. Por favor, contacte al administrador si necesita acceso.'
                }, status=403)
        
        # Si no es PermissionDenied o no es AJAX, dejar que Django maneje el error normalmente
        return None


