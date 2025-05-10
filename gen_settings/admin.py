from django.contrib import admin
from .models import Region, Comuna, Empresa

# Register your models here.

admin.site.register(Region)
admin.site.register(Comuna)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    # Definir los campos que se mostrarán en el formulario
    fields = ('comuna_id', 'rut', 'dvRut', 'razonSocial', 'nombreFant', 'giro', 'direccion', 'telefono')
    list_display = ('razonSocial', 'rut', 'telefono')
    search_fields = ('razonSocial', 'rut', 'nombreFant', 'direccion')