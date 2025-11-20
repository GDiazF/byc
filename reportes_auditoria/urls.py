from django.urls import path
from . import views

app_name = 'reportes_auditoria'

urlpatterns = [
    # Auditoría - Historial consolidado
    path('auditoria/', views.auditoria_view, name='auditoria'),
    path('api/auditoria/', views.api_auditoria, name='api_auditoria'),
    
    # Reportabilidad - Consultas estadísticas
    path('reportabilidad/', views.reportabilidad_view, name='reportabilidad'),
    path('api/reportabilidad/', views.api_reportabilidad, name='api_reportabilidad'),
]

