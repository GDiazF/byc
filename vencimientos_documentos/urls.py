"""
URLs para la app de vencimientos de documentos.
"""

from django.urls import path
from . import views

app_name = 'vencimientos_documentos'

urlpatterns = [
    path('', views.vencimientos_view, name='vencimientos'),
    path('api/personal/', views.api_vencimientos_personal, name='api_vencimientos_personal'),
    path('api/maquinarias/', views.api_vencimientos_maquinarias, name='api_vencimientos_maquinarias'),
    path('api/exportar/personal/', views.exportar_excel_personal, name='exportar_excel_personal'),
    path('api/exportar/maquinarias/', views.exportar_excel_maquinarias, name='exportar_excel_maquinarias'),
]

