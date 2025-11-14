from django.contrib import admin
from .models import (
    TipoEquipo, MarcaEquipo, ModeloEquipo, Equipo,
    Seccion, TipoReparacion, PautaMantenimientoPreventivo, ItemPauta,
    TipoDocumentoMaquinaria, DocumentoMaquinaria, HistorialDocumentoMaquinaria,
    TipoMantenimiento, EstadoOT, EstadoEquipo,
    OrdenTrabajo, ItemSeccionOT, HistorialObservacionesOT, HistorialOT
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


# ==================== MODELOS DE DOCUMENTACIÓN ====================

@admin.register(TipoDocumentoMaquinaria)
class TipoDocumentoMaquinariaAdmin(admin.ModelAdmin):
    list_display = ('tipoDocumento_id', 'nombre', 'requiere_fecha_vencimiento', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'requiere_fecha_vencimiento', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    ordering = ('nombre',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'requiere_fecha_vencimiento', 'activo')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentoMaquinaria)
class DocumentoMaquinariaAdmin(admin.ModelAdmin):
    list_display = ('documento_id', 'equipo_id', 'tipo_documento_id', 'fecha_vencimiento', 'fecha_subida', 'estado_documento')
    list_filter = ('tipo_documento_id', 'fecha_vencimiento', 'fecha_subida')
    search_fields = ('equipo_id__nombreEquipo', 'tipo_documento_id__nombre', 'observaciones')
    readonly_fields = ('fecha_subida',)
    ordering = ('-fecha_subida',)
    
    fieldsets = (
        ('Información del Documento', {
            'fields': ('equipo_id', 'tipo_documento_id', 'archivo', 'fecha_vencimiento', 'observaciones')
        }),
        ('Auditoría', {
            'fields': ('fecha_subida',),
            'classes': ('collapse',)
        }),
    )
    
    def estado_documento(self, obj):
        if obj.esta_vencido:
            return 'Vencido'
        elif obj.esta_por_vencer:
            return 'Por vencer'
        else:
            return 'Vigente'
    estado_documento.short_description = 'Estado'


@admin.register(HistorialDocumentoMaquinaria)
class HistorialDocumentoMaquinariaAdmin(admin.ModelAdmin):
    list_display = ('historial_id', 'equipo_id', 'tipo_documento_nombre', 'fecha_vencimiento', 'fecha_reemplazo')
    list_filter = ('tipo_documento_id', 'fecha_reemplazo', 'fecha_vencimiento')
    search_fields = ('equipo_id__nombreEquipo', 'tipo_documento_nombre', 'observaciones')
    readonly_fields = ('fecha_reemplazo',)
    ordering = ('-fecha_reemplazo',)
    
    fieldsets = (
        ('Información del Documento', {
            'fields': ('equipo_id', 'tipo_documento_id', 'tipo_documento_nombre', 'archivo', 
                      'fecha_vencimiento', 'fecha_subida_original', 'observaciones')
        }),
        ('Auditoría', {
            'fields': ('fecha_reemplazo',),
            'classes': ('collapse',)
        }),
    )


# ==================== MODELOS DE ORDEN DE TRABAJO ====================

@admin.register(TipoMantenimiento)
class TipoMantenimientoAdmin(admin.ModelAdmin):
    list_display = ('tipoMantenimiento_id', 'nombre', 'descripcion', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)


@admin.register(EstadoOT)
class EstadoOTAdmin(admin.ModelAdmin):
    list_display = ('estadoOT_id', 'nombre', 'color', 'orden', 'activo')
    list_filter = ('activo', 'color')
    search_fields = ('nombre', 'descripcion')
    ordering = ('orden', 'nombre')


@admin.register(EstadoEquipo)
class EstadoEquipoAdmin(admin.ModelAdmin):
    list_display = ('estadoEquipo_id', 'nombre', 'color', 'orden', 'activo')
    list_filter = ('activo', 'color')
    search_fields = ('nombre', 'descripcion')
    ordering = ('orden', 'nombre')


# ==================== MODELOS DE ORDEN DE TRABAJO ====================

class ItemSeccionOTInline(admin.TabularInline):
    model = ItemSeccionOT
    extra = 0
    filter_horizontal = ('tipos_reparacion',)
    fields = ('seccion_id', 'tipos_reparacion', 'estado_seccion_id')
    readonly_fields = ()


class HistorialObservacionesOTInline(admin.TabularInline):
    model = HistorialObservacionesOT
    extra = 0
    fields = ('observacion', 'usuario', 'fecha')
    readonly_fields = ('fecha',)
    can_delete = False


@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ('folio', 'equipo_id', 'empresa_id', 'tipo_mantenimiento_id', 'estado_ot_id', 'estado_equipo_id', 'fecha_creacion', 'fecha_inicio', 'fecha_fin')
    list_filter = ('estado_ot_id', 'estado_equipo_id', 'tipo_mantenimiento_id', 'empresa_id', 'fecha_creacion')
    search_fields = ('folio', 'equipo_id__nombreEquipo', 'equipo_id__codigoInterno', 'observaciones')
    readonly_fields = ('folio', 'fecha_creacion')
    filter_horizontal = ('personal_asignado',)
    ordering = ('-fecha_creacion',)
    inlines = [ItemSeccionOTInline, HistorialObservacionesOTInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('folio', 'equipo_id', 'empresa_id', 'tipo_mantenimiento_id', 'fecha_creacion')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Datos del Equipo (Automáticos)', {
            'fields': ('horometro', 'odometro', 'horometro_superestructura'),
            'classes': ('collapse',)
        }),
        ('Mantenimiento Preventivo', {
            'fields': ('corresponde_pauta', 'pauta_id'),
            'classes': ('collapse',)
        }),
        ('Estados', {
            'fields': ('estado_ot_id', 'estado_equipo_id')
        }),
        ('Personal Asignado', {
            'fields': ('personal_asignado',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )
    
    def delete_model(self, request, obj):
        """Permitir eliminación de OT y sus objetos relacionados (incluyendo HistorialOT)"""
        # Eliminar objetos relacionados manualmente para evitar problemas de permisos
        obj.historial.all().delete()  # Eliminar HistorialOT relacionado
        obj.items_secciones.all().delete()  # Eliminar ItemSeccionOT relacionado
        obj.historial_observaciones.all().delete()  # Eliminar HistorialObservacionesOT relacionado
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        """Permitir eliminación masiva de OTs y sus objetos relacionados"""
        from django.db import transaction
        with transaction.atomic():
            for obj in queryset:
                # Eliminar objetos relacionados manualmente para evitar problemas de permisos
                obj.historial.all().delete()  # Eliminar HistorialOT relacionado
                obj.items_secciones.all().delete()  # Eliminar ItemSeccionOT relacionado
                obj.historial_observaciones.all().delete()  # Eliminar HistorialObservacionesOT relacionado
            queryset.delete()


@admin.register(ItemSeccionOT)
class ItemSeccionOTAdmin(admin.ModelAdmin):
    list_display = ('itemSeccionOT_id', 'ot_id', 'seccion_id', 'estado_seccion_id', 'total_tipos_reparacion')
    list_filter = ('ot_id', 'seccion_id', 'estado_seccion_id')
    search_fields = ('ot_id__folio', 'seccion_id__nombre')
    filter_horizontal = ('tipos_reparacion',)
    ordering = ('ot_id', 'seccion_id')
    
    def total_tipos_reparacion(self, obj):
        return obj.tipos_reparacion.count()
    total_tipos_reparacion.short_description = 'Tipos de Reparación'


@admin.register(HistorialObservacionesOT)
class HistorialObservacionesOTAdmin(admin.ModelAdmin):
    list_display = ('historial_id', 'ot_id', 'usuario', 'fecha', 'observacion_preview')
    list_filter = ('ot_id', 'usuario', 'fecha')
    search_fields = ('ot_id__folio', 'observacion')
    readonly_fields = ('fecha',)
    ordering = ('-fecha',)
    
    def observacion_preview(self, obj):
        return obj.observacion[:100] + '...' if len(obj.observacion) > 100 else obj.observacion
    observacion_preview.short_description = 'Observación'


@admin.register(HistorialOT)
class HistorialOTAdmin(admin.ModelAdmin):
    list_display = ['ot', 'fecha_hora', 'accion', 'usuario', 'descripcion_corta']
    list_filter = ['accion', 'fecha_hora', 'ot']
    search_fields = ['ot__folio', 'descripcion', 'usuario__username']
    date_hierarchy = 'fecha_hora'
    ordering = ['-fecha_hora']
    readonly_fields = ['fecha_hora', 'ot', 'usuario', 'accion', 'descripcion', 'datos_previos', 'datos_nuevos']
    
    fieldsets = (
        ('Información del Registro', {
            'fields': ('ot', 'fecha_hora', 'usuario', 'accion')
        }),
        ('Detalles', {
            'fields': ('descripcion',)
        }),
        ('Datos Técnicos', {
            'fields': ('datos_previos', 'datos_nuevos'),
            'classes': ('collapse',)
        }),
    )
    
    def descripcion_corta(self, obj):
        if obj.descripcion:
            return obj.descripcion[:80] + "..." if len(obj.descripcion) > 80 else obj.descripcion
        return "-"
    descripcion_corta.short_description = "Descripción"
    
    def has_add_permission(self, request):
        # No permitir crear manualmente desde admin (se crea automáticamente)
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Permitir eliminación solo si el usuario es superuser (para pruebas y limpieza)
        # En producción, esto debería ser False para mantener la integridad de auditoría
        return request.user.is_superuser
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ot', 'usuario')
