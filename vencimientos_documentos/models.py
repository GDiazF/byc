"""
============================================================================
MODELOS PARA LA APP DE VENCIMIENTOS DE DOCUMENTOS
============================================================================
Este módulo define el modelo VencimientoDocumento, que es un modelo ficticio
utilizado únicamente para generar permisos automáticos de Django. No se usa
directamente para almacenar datos, solo para definir permisos personalizados.
============================================================================
"""

from django.db import models


# Este modelo es solo para crear permisos automáticos de Django
# No se usa directamente, pero permite que Django cree permisos como:
# vencimientos_documentos.view_vencimientos
class VencimientoDocumento(models.Model):
    """
    Modelo ficticio para generar permisos automáticos de Django.
    
    Este modelo no se usa directamente para almacenar datos. Su único propósito
    es permitir que Django genere permisos personalizados para la aplicación
    de vencimientos de documentos, específicamente el permiso 'view_vencimientos'.
    
    Los datos reales de vencimientos se obtienen dinámicamente desde los modelos
    de Personal y Equipo en otras aplicaciones.
    """
    class Meta:
        verbose_name = "Vencimiento de Documento"
        verbose_name_plural = "Vencimientos de Documentos"
        permissions = [
            ('view_vencimientos', 'Puede ver el panel de vencimientos de documentos'),
        ]
