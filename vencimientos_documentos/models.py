"""
Modelos para la app de vencimientos de documentos.
"""

from django.db import models


# Este modelo es solo para crear permisos automáticos de Django
# No se usa directamente, pero permite que Django cree permisos como:
# vencimientos_documentos.view_vencimientos
class VencimientoDocumento(models.Model):
    """
    Modelo ficticio para generar permisos automáticos de Django.
    No se usa directamente, solo para permisos.
    """
    class Meta:
        verbose_name = "Vencimiento de Documento"
        verbose_name_plural = "Vencimientos de Documentos"
        permissions = [
            ('view_vencimientos', 'Puede ver el panel de vencimientos de documentos'),
        ]
