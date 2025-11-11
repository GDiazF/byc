from django.contrib import admin
from .models import (
    TipoEquipo, MarcaEquipo, ModeloEquipo, Equipo,
    Seccion, TipoReparacion, PautaMantenimientoPreventivo, ItemPauta
)


# ==================== MODELOS DE EQUIPOS ====================

@admin.register(TipoEquipo)
class TipoEquipoAdmin(admin.ModelAdmin):
    list_display = ('tipoEquipo_id', 'tipoEquipo', 'siglaEquipo')
    search_fields = ('tipoEquipo', 'siglaEquipo')
    ordering = ('tipoEquipo',)


@admin.register(MarcaEquipo)
class MarcaEquipoAdmin(admin.ModelAdmin):
    list_display = ('marcaEquipo_id', 'marcaEquipo')
    search_fields = ('marcaEquipo',)
    ordering = ('marcaEquipo',)


@admin.register(ModeloEquipo)
class ModeloEquipoAdmin(admin.ModelAdmin):
    list_display = ('modeloEquipo_id', 'modeloEquipo', 'tipoEquipo_id', 'marcaEquipo_id')
    list_filter = ('tipoEquipo_id', 'marcaEquipo_id')
    search_fields = ('modeloEquipo',)
    ordering = ('modeloEquipo',)


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('equipo_id', 'nombreEquipo', 'modeloEquipo_id', 'empresa_id', 'codigoInterno', 'patente', 'activo')
    list_filter = ('activo', 'empresa_id', 'modeloEquipo_id__tipoEquipo_id')
    search_fields = ('nombreEquipo', 'codigoInterno', 'patente')
    readonly_fields = ('nombreEquipo',)
    ordering = ('-activo', 'nombreEquipo')


# ==================== MODELOS DE MANTENIMIENTO ====================

@admin.register(Seccion)
class SeccionAdmin(admin.ModelAdmin):
    list_display = ('seccion_id', 'nombre', 'descripcion', 'total_tipos_reparacion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)
    
    def total_tipos_reparacion(self, obj):
        return obj.tipos_reparacion.count()
    total_tipos_reparacion.short_description = 'Tipos de Reparación'


@admin.register(TipoReparacion)
class TipoReparacionAdmin(admin.ModelAdmin):
    list_display = ('tipoReparacion_id', 'nombre', 'seccion_id', 'descripcion')
    list_filter = ('seccion_id',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('seccion_id', 'nombre')


class ItemPautaInline(admin.TabularInline):
    model = ItemPauta
    extra = 1
    filter_horizontal = ('tipos_reparacion',)


@admin.register(PautaMantenimientoPreventivo)
class PautaMantenimientoPreventivoAdmin(admin.ModelAdmin):
    list_display = ('pauta_id', 'nombre', 'modeloEquipo_id', 'activo', 'fecha_creacion', 'fecha_modificacion')
    list_filter = ('activo', 'modeloEquipo_id__tipoEquipo_id', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    ordering = ('-activo', 'nombre')
    inlines = [ItemPautaInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'modeloEquipo_id', 'descripcion', 'activo')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ItemPauta)
class ItemPautaAdmin(admin.ModelAdmin):
    list_display = ('itemPauta_id', 'pauta_id', 'seccion_id', 'total_tipos_reparacion')
    list_filter = ('pauta_id', 'seccion_id')
    filter_horizontal = ('tipos_reparacion',)
    ordering = ('pauta_id', 'seccion_id')
    
    def total_tipos_reparacion(self, obj):
        return obj.tipos_reparacion.count()
    total_tipos_reparacion.short_description = 'Tipos de Reparación'
