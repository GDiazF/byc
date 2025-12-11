from django.apps import AppConfig


class ReportesAuditoriaConfig(AppConfig):
    """
    Configuración de la aplicación reportes_auditoria.
    
    Esta aplicación proporciona funcionalidades de auditoría y reportabilidad
    del sistema, permitiendo consultar historiales consolidados de eventos
    y generar reportes estadísticos de diferentes entidades.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reportes_auditoria'
