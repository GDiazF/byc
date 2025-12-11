from django.urls import path
from . import views

app_name = 'reportes_auditoria'

urlpatterns = [
    # ========================================================================
    # AUDITORÍA - Historial consolidado de eventos del sistema
    # ========================================================================
    
    # Vista principal de auditoría - página HTML con filtros y tabla de eventos
    path('auditoria/', views.auditoria_view, name='auditoria'),
    
    # API para obtener eventos de auditoría con filtros y paginación (AJAX)
    path('api/auditoria/', views.api_auditoria, name='api_auditoria'),
    
    # ========================================================================
    # REPORTABILIDAD - Consultas estadísticas y reportes
    # ========================================================================
    
    # Vista principal de reportabilidad - página HTML con opciones de reportes
    path('reportabilidad/', views.reportabilidad_view, name='reportabilidad'),
    
    # API para generar reportes estadísticos (AJAX)
    path('api/reportabilidad/', views.api_reportabilidad, name='api_reportabilidad'),
]

