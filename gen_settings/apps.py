"""
============================================================================
CONFIGURACIÓN DE LA APLICACIÓN GEN_SETTINGS
============================================================================
Configuración de la aplicación Django para configuraciones generales del sistema.
============================================================================
"""

from django.apps import AppConfig


class GenSettingsConfig(AppConfig):
    """
    Configuración de la aplicación gen_settings.
    
    Esta aplicación gestiona las configuraciones generales del sistema,
    incluyendo regiones, comunas, empresas y unidades de medida que son
    utilizadas por otras aplicaciones del sistema.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gen_settings'
