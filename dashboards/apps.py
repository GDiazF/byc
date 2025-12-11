# ============================================================================
# CONFIGURACION DE LA APLICACION DASHBOARDS
# ============================================================================
# Este archivo contiene la configuracion de la aplicacion dashboards.
# ============================================================================

from django.apps import AppConfig


class DashboardsConfig(AppConfig):
    """
    Configuración de la aplicación Dashboards.
    
    Esta aplicación gestiona los dashboards del sistema organizados por áreas:
    - RRHH: Recursos Humanos
    - Operaciones: Planificación y faenas
    - Maquinarias: Equipos y órdenes de trabajo
    - Gerencia: Métricas consolidadas y KPIs estratégicos
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboards'
