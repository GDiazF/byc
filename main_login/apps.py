# ============================================================================
# CONFIGURACIÓN DE LA APLICACIÓN MAIN_LOGIN
# ============================================================================

from django.apps import AppConfig


class MainLoginConfig(AppConfig):
    """
    Configuración de la aplicación main_login.
    
    Esta aplicación gestiona el sistema de autenticación personalizado,
    incluyendo la vista de login con detección de intentos fallidos y
    creación de notificaciones de seguridad.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main_login'
