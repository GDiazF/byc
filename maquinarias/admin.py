from django.contrib import admin
from .models import TipoEquipo, MarcaEquipo, ModeloEquipo, Equipo


@admin.register(TipoEquipo)
class TipoEquipoAdmin(admin.ModelAdmin):
    list_display = ('tipoEquipo', 'siglaEquipo')
    search_fields = ('tipoEquipo', 'siglaEquipo')
    ordering = ('tipoEquipo',)


@admin.register(MarcaEquipo)
class MarcaEquipoAdmin(admin.ModelAdmin):
    list_display = ('marcaEquipo',)
    search_fields = ('marcaEquipo',)
    ordering = ('marcaEquipo',)


@admin.register(ModeloEquipo)
class ModeloEquipoAdmin(admin.ModelAdmin):
    list_display = ('modeloEquipo', 'tipoEquipo_id', 'marcaEquipo_id')
    list_filter = ('tipoEquipo_id', 'marcaEquipo_id')
    search_fields = ('modeloEquipo',)
    ordering = ('tipoEquipo_id', 'marcaEquipo_id', 'modeloEquipo')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tipoEquipo_id', 'marcaEquipo_id')


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombreEquipo', 'get_tipo', 'get_marca', 'get_modelo', 'codigoInterno', 'patente', 'activo')
    list_filter = ('activo', 'empresa_id', 'modeloEquipo_id__tipoEquipo_id', 'modeloEquipo_id__marcaEquipo_id')
    search_fields = ('nombreEquipo', 'codigoInterno', 'patente')
    readonly_fields = ('nombreEquipo',)
    ordering = ('-activo', 'nombreEquipo')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('empresa_id', 'modeloEquipo_id', 'codigoInterno', 'patente', 'nombreEquipo')
        }),
        ('Mediciones', {
            'fields': ('horometro', 'odometro', 'horometroSuperEstructural')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'empresa_id',
            'modeloEquipo_id',
            'modeloEquipo_id__tipoEquipo_id',
            'modeloEquipo_id__marcaEquipo_id'
        )
    
    def get_tipo(self, obj):
        return obj.modeloEquipo_id.tipoEquipo_id.tipoEquipo
    get_tipo.short_description = 'Tipo'
    get_tipo.admin_order_field = 'modeloEquipo_id__tipoEquipo_id__tipoEquipo'
    
    def get_marca(self, obj):
        return obj.modeloEquipo_id.marcaEquipo_id.marcaEquipo
    get_marca.short_description = 'Marca'
    get_marca.admin_order_field = 'modeloEquipo_id__marcaEquipo_id__marcaEquipo'
    
    def get_modelo(self, obj):
        return obj.modeloEquipo_id.modeloEquipo
    get_modelo.short_description = 'Modelo'
    get_modelo.admin_order_field = 'modeloEquipo_id__modeloEquipo'
