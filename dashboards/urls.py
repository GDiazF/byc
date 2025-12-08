# ============================================================================
# URLS PARA DASHBOARDS
# ============================================================================
# Este archivo define las rutas URL para la aplicacion de dashboards.
# Incluye la vista principal y las APIs para obtener datos de cada area.
# ============================================================================

from django.urls import path
from . import views

app_name = 'dashboards'

urlpatterns = [
    # Vista principal de dashboards
    path('', views.dashboards_view, name='dashboards'),
    
    # APIs para obtener datos de cada area
    path('api/rrhh/', views.api_dashboard_rrhh, name='api_dashboard_rrhh'),
    path('api/operaciones/', views.api_dashboard_operaciones, name='api_dashboard_operaciones'),
    path('api/maquinarias/', views.api_dashboard_maquinarias, name='api_dashboard_maquinarias'),
    path('api/gerencia/', views.api_dashboard_gerencia, name='api_dashboard_gerencia'),
]

