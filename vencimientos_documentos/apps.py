"""
============================================================================
CONFIGURACIÓN DE LA APLICACIÓN VENCIMIENTOS_DOCUMENTOS
============================================================================
Configuración de la aplicación Django para el módulo de vencimientos de documentos.
============================================================================
"""

from django.apps import AppConfig


class VencimientosDocumentosConfig(AppConfig):
    """
    Configuración de la aplicación vencimientos_documentos.
    
    Esta aplicación gestiona la visualización y exportación de documentos
    próximos a vencer de personal y maquinarias, permitiendo a los usuarios
    monitorear y gestionar los vencimientos de manera centralizada.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vencimientos_documentos'
