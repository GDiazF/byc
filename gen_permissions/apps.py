from django.apps import AppConfig


# ============================================================================
# CONFIGURACION DE LA APLICACION GEN_PERMISSIONS
# ============================================================================
# Esta clase configura la app y asegura que los signals se registren
# correctamente cuando Django carga la app.
# ============================================================================

from django.apps import AppConfig


class GenPermissionsConfig(AppConfig):
    # Configuracion de la app gen_permissions.
    # Esta clase configura la app y asegura que los signals se registren
    # correctamente cuando Django carga la app.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gen_permissions'
    
    def ready(self):
        # Metodo que se ejecuta cuando Django carga la app.
        # Importa los signals para asegurar que se registren correctamente.
        # Importar signals para que se registren
        import gen_permissions.signals  # noqa
