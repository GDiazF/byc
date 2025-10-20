from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Estado, EstadoFuente, Turno, TurnoBloque, Faena, AsignacionFaena, EstadoManual
)

# ============================================================================
# ADMIN PARA MODELOS DE CALENDARIO
# ============================================================================

@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nombre_corto', 'color_preview', 'background_color_preview', 'prioridad', 'es_bloqueante', 'es_predeterminado', 'activo']
    list_filter = ['activo', 'es_bloqueante', 'es_predeterminado', 'prioridad']
    search_fields = ['nombre', 'nombre_corto']
    ordering = ['-activo', '-prioridad', 'nombre']
    
    fieldsets = (
        ('Información del Estado', {
            'fields': ('nombre', 'nombre_corto', 'activo')
        }),
        ('Visualización', {
            'fields': ('color', 'background_color')
        }),
        ('Comportamiento', {
            'fields': ('prioridad', 'es_bloqueante', 'es_predeterminado')
        }),
    )
    
    def color_preview(self, obj):
        if obj.color:
            return format_html(
                '<div style="background-color: {}; width: 30px; height: 20px; border: 1px solid #ccc; border-radius: 3px;"></div>',
                obj.color
            )
        return "-"
    color_preview.short_description = "Color Texto"
    
    def background_color_preview(self, obj):
        if obj.background_color:
            return format_html(
                '<div style="background-color: {}; width: 30px; height: 20px; border: 1px solid #ccc; border-radius: 3px;"></div>',
                obj.background_color
            )
        return "-"
    background_color_preview.short_description = "Color Fondo"

@admin.register(EstadoFuente)
class EstadoFuenteAdmin(admin.ModelAdmin):
    list_display = ['estado', 'content_type', 'campo_fecha_inicio', 'campo_fecha_fin', 'campo_personal']
    list_filter = ['estado__activo', 'content_type']
    search_fields = ['estado__nombre']
    ordering = ['estado__nombre']
    
    fieldsets = (
        ('Estado Asociado', {
            'fields': ('estado',)
        }),
        ('Configuración de Fuente', {
            'fields': ('content_type', 'campo_fecha_inicio', 'campo_fecha_fin', 'campo_personal')
        }),
    )

class TurnoBloqueInline(admin.TabularInline):
    model = TurnoBloque
    extra = 1
    ordering = ['orden']
    fields = ['orden', 'duracion_dias', 'estado']

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'longitud_ciclo', 'activo', 'descripcion_short', 'cantidad_bloques']
    list_filter = ['activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    inlines = [TurnoBloqueInline]
    
    fieldsets = (
        ('Información del Turno', {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
    )
    
    def descripcion_short(self, obj):
        if obj.descripcion:
            return obj.descripcion[:50] + "..." if len(obj.descripcion) > 50 else obj.descripcion
        return "-"
    descripcion_short.short_description = "Descripción"
    
    def cantidad_bloques(self, obj):
        count = obj.bloques.count()
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-weight: bold;">{} bloque{}</span>',
            count, 's' if count != 1 else ''
        )
    cantidad_bloques.short_description = "Bloques"

@admin.register(TurnoBloque)
class TurnoBloqueAdmin(admin.ModelAdmin):
    list_display = ['turno', 'orden', 'duracion_dias', 'estado', 'estado_color_preview']
    list_filter = ['turno', 'estado', 'estado__activo']
    ordering = ['turno', 'orden']
    search_fields = ['turno__nombre', 'estado__nombre']
    
    fieldsets = (
        ('Información del Bloque', {
            'fields': ('turno', 'orden', 'duracion_dias')
        }),
        ('Estado Asociado', {
            'fields': ('estado',)
        }),
    )
    
    def estado_color_preview(self, obj):
        if obj.estado and obj.estado.background_color:
            return format_html(
                '<div style="background-color: {}; color: {}; padding: 2px 6px; border-radius: 3px; '
                'font-size: 11px; font-weight: bold; display: inline-block;">{}</div>',
                obj.estado.background_color,
                obj.estado.color,
                obj.estado.nombre
            )
        return obj.estado.nombre if obj.estado else "-"
    estado_color_preview.short_description = "Vista Previa"

@admin.register(Faena)
class FaenaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ubicacion', 'activo', 'descripcion_short', 'asignaciones_count']
    list_filter = ['activo']
    search_fields = ['nombre', 'ubicacion', 'descripcion']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información de la Faena', {
            'fields': ('nombre', 'ubicacion', 'descripcion', 'activo')
        }),
    )
    
    def descripcion_short(self, obj):
        if obj.descripcion:
            return obj.descripcion[:50] + "..." if len(obj.descripcion) > 50 else obj.descripcion
        return "-"
    descripcion_short.short_description = "Descripción"
    
    def asignaciones_count(self, obj):
        count = obj.asignaciones_faena.filter(activo=True).count()
        color = '#27ae60' if count > 0 else '#95a5a6'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-weight: bold;">{} asignación{}</span>',
            color, count, 'es' if count != 1 else ''
        )
    asignaciones_count.short_description = "Asignaciones Activas"

@admin.register(AsignacionFaena)
class AsignacionFaenaAdmin(admin.ModelAdmin):
    list_display = [
        'personal', 'faena', 'turno', 'fecha_inicio', 'fecha_fin', 
        'bloque_inicio', 'duracion_dias', 'activo', 'tiene_observaciones'
    ]
    list_filter = ['activo', 'faena', 'turno', 'fecha_inicio', 'fecha_fin']
    search_fields = ['personal__nombre', 'personal__apepat', 'faena__nombre', 'turno__nombre', 'observaciones']
    date_hierarchy = 'fecha_inicio'
    ordering = ['personal', '-fecha_inicio']
    
    fieldsets = (
        ('Asignación', {
            'fields': ('personal', 'faena', 'turno', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Configuración del Turno', {
            'fields': ('bloque_inicio',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    
    def duracion_dias(self, obj):
        if obj.fecha_inicio and obj.fecha_fin:
            delta = obj.fecha_fin - obj.fecha_inicio
            dias = delta.days + 1
            return f"{dias} día{'s' if dias != 1 else ''}"
        elif obj.fecha_inicio:
            return "Sin fecha fin"
        return "-"
    duracion_dias.short_description = "Duración"
    
    def tiene_observaciones(self, obj):
        if obj.observaciones:
            return format_html(
                '<span style="color: #3498db;" title="{}">📝 Sí</span>',
                obj.observaciones[:100] + "..." if len(obj.observaciones) > 100 else obj.observaciones
            )
        return format_html('<span style="color: #95a5a6;">-</span>')
    tiene_observaciones.short_description = "Observaciones"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('personal', 'faena', 'turno', 'bloque_inicio')

@admin.register(EstadoManual)
class EstadoManualAdmin(admin.ModelAdmin):
    list_display = [
        'personal', 'estado', 'fecha_inicio', 'fecha_fin', 
        'duracion_dias', 'motivo_short', 'activo', 'creado_en'
    ]
    list_filter = ['activo', 'estado', 'fecha_inicio', 'fecha_fin', 'creado_en']
    search_fields = ['personal__nombre', 'personal__apepat', 'personal__apemat', 'motivo']
    date_hierarchy = 'fecha_inicio'
    ordering = ['-creado_en', 'personal']
    readonly_fields = ['creado_en']
    
    fieldsets = (
        ('Información del Estado Manual', {
            'fields': ('personal', 'estado', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Detalles', {
            'fields': ('motivo',)
        }),
        ('Metadatos', {
            'fields': ('creado_en',),
            'classes': ('collapse',)
        }),
    )
    
    def duracion_dias(self, obj):
        if obj.fecha_inicio and obj.fecha_fin:
            delta = obj.fecha_fin - obj.fecha_inicio
            dias = delta.days + 1
            return format_html(
                '<span style="font-weight: bold;">{} día{}</span>',
                dias, 's' if dias != 1 else ''
            )
        elif obj.fecha_inicio:
            return "Sin fecha fin"
        return "-"
    duracion_dias.short_description = "Duración"
    
    def motivo_short(self, obj):
        if obj.motivo:
            return obj.motivo[:50] + "..." if len(obj.motivo) > 50 else obj.motivo
        return "-"
    motivo_short.short_description = "Motivo"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('personal', 'estado')

# ============================================================================
# PERSONALIZACIÓN DEL SITE ADMIN
# ============================================================================

admin.site.site_header = "Administración del Calendario de Planificación"
admin.site.site_title = "Calendario Admin"
admin.site.index_title = "Panel de Control del Calendario"
