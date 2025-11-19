from django.apps import AppConfig


class MaquinariasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'maquinarias'
    
    def ready(self):
        import maquinarias.signals  # noqa