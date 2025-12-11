"""
Configuración de la aplicación maquinarias.

Este módulo define la configuración de la app maquinarias, incluyendo
la importación de signals para que se registren automáticamente cuando
Django carga la aplicación.
"""

from django.apps import AppConfig


class MaquinariasConfig(AppConfig):
    """
    Configuración de la aplicación maquinarias.
    
    Esta clase configura la app y asegura que los signals se registren
    correctamente cuando Django carga la app. Los signals se importan en el
    método ready() para garantizar que se registren después de que Django
    esté completamente inicializado.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'maquinarias'
    
    def ready(self):
        """
        Método que se ejecuta cuando Django está listo.
        
        Importa los signals de la app para que se registren automáticamente.
        """
        import maquinarias.signals  # noqa