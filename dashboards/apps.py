# ============================================================================
# CONFIGURACION DE LA APLICACION DASHBOARDS
# ============================================================================
# Este archivo contiene la configuracion de la aplicacion dashboards.
# ============================================================================

from django.apps import AppConfig


class DashboardsConfig(AppConfig):
    # Configuracion de la aplicacion Dashboards.
    # Define el nombre de la aplicacion y el campo auto por defecto.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboards'
