"""
============================================================================
URLS PARA LA APP DE VENCIMIENTOS DE DOCUMENTOS
============================================================================
Define las rutas URL para la aplicación de vencimientos de documentos:
- Vista principal del panel
- APIs para obtener documentos de personal y maquinarias
- Endpoints para exportar a Excel
- Endpoint para ejecutar procesamiento manual de vencimientos
============================================================================
"""

from django.urls import path
from . import views

app_name = 'vencimientos_documentos'

urlpatterns = [
    # Vista principal del panel de vencimientos
    path('', views.vencimientos_view, name='vencimientos'),
    
    # APIs para obtener documentos próximos a vencer
    path('api/personal/', views.api_vencimientos_personal, name='api_vencimientos_personal'),
    path('api/maquinarias/', views.api_vencimientos_maquinarias, name='api_vencimientos_maquinarias'),
    
    # Endpoints para exportar a Excel
    path('api/exportar/personal/', views.exportar_excel_personal, name='exportar_excel_personal'),
    path('api/exportar/maquinarias/', views.exportar_excel_maquinarias, name='exportar_excel_maquinarias'),
    
    # Endpoint para ejecutar procesamiento manual (solo para pruebas)
    path('api/ejecutar-procesamiento/', views.ejecutar_procesar_vencimientos, name='ejecutar_procesar_vencimientos'),
]

