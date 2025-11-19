from django.apps import AppConfig


class RrhhPersonalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rrhh_personal'
    
    def ready(self):
        import rrhh_personal.signals  # noqa