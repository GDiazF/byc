# ============================================================================
# CONFIGURACIÓN DE LA APLICACIÓN MAIN_HOME
# ============================================================================

from django.apps import AppConfig


class MainhomeConfig(AppConfig):
    """
    Configuración de la aplicación main_home.
    
    Esta aplicación gestiona la página principal del sistema después del login,
    el perfil del usuario y el cambio de contraseña.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main_home'
