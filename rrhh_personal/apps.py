"""
Configuración de la aplicación rrhh_personal.

Define la configuración de la app y asegura que los signals
se registren cuando la app esté lista.
"""
from django.apps import AppConfig


class RrhhPersonalConfig(AppConfig):
    """
    Configuración de la aplicación de gestión de personal (RRHH).
    
    Esta clase configura la aplicación y registra los signals
    necesarios para el funcionamiento del módulo de personal.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rrhh_personal'
    
    def ready(self):
        """
        Método llamado cuando la aplicación está lista.
        
        Importa los signals para que se registren automáticamente
        y puedan escuchar eventos de los modelos.
        """
        import rrhh_personal.signals  # noqa