"""
============================================================================
ADMIN PARA GEN_SETTINGS
============================================================================
Configuración del panel de administración de Django para los modelos
de configuraciones generales: Region, Comuna, Empresa y UnidadMedida.
============================================================================
"""

from django.contrib import admin
from .models import Region, Comuna, Empresa

# Registrar modelos básicos con configuración por defecto
admin.site.register(Region)
admin.site.register(Comuna)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Empresa.
    
    Define los campos que se mostrarán en el formulario y en la lista,
    así como los campos de búsqueda.
    """
    fields = ('region', 'comuna', 'rut', 'dv', 'razonSocial', 'nomFantasia', 'giro', 'direccion', 'telefono', 'email')
    list_display = ('razonSocial', 'rut', 'telefono', 'email')
    search_fields = ('razonSocial', 'rut', 'nomFantasia', 'direccion')