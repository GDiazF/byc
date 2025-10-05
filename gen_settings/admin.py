from django.contrib import admin
from .models import Region, Comuna, Empresa

# Register your models here.

admin.site.register(Region)
admin.site.register(Comuna)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    # Definir los campos que se mostrarán en el formulario
    fields = ('region', 'comuna', 'rut', 'dv', 'razonSocial', 'nomFantasia', 'giro', 'direccion', 'telefono', 'email')
    list_display = ('razonSocial', 'rut', 'telefono', 'email')
    search_fields = ('razonSocial', 'rut', 'nomFantasia', 'direccion')