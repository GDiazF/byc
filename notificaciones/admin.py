# ============================================================================
# ADMIN PARA EL SISTEMA DE NOTIFICACIONES
# ============================================================================
# Configuración del admin para gestionar tipos de notificaciones,
# notificaciones y configuraciones por rol
# ============================================================================

from django.contrib import admin
from .models import TipoNotificacion, Notificacion, ConfiguracionNotificacionRol


@admin.register(TipoNotificacion)
class TipoNotificacionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'prioridad', 'activo')
    list_filter = ('categoria', 'prioridad', 'activo')
    search_fields = ('codigo', 'nombre', 'descripcion')
    ordering = ('categoria', 'nombre')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria', 'prioridad', 'activo')
        }),
        ('Templates', {
            'fields': ('template_titulo', 'template_mensaje'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'titulo', 'tipo_notificacion', 'leida', 'prioridad', 'fecha_creacion')
    list_filter = ('tipo_notificacion', 'leida', 'prioridad', 'archivada', 'fecha_creacion')
    search_fields = ('titulo', 'mensaje', 'usuario__username', 'usuario__email')
    readonly_fields = ('fecha_creacion', 'fecha_leida', 'fecha_archivada')
    ordering = ('-fecha_creacion',)
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'tipo_notificacion', 'titulo', 'mensaje', 'prioridad')
        }),
        ('Estado', {
            'fields': ('leida', 'fecha_leida', 'archivada', 'fecha_archivada')
        }),
        ('Datos Adicionales', {
            'fields': ('datos_adicionales',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )
    
    def fecha_leida(self, obj):
        return obj.fecha_leida
    fecha_leida.short_description = 'Fecha de Lectura'
    
    def fecha_archivada(self, obj):
        return obj.fecha_archivada
    fecha_archivada.short_description = 'Fecha de Archivado'


@admin.register(ConfiguracionNotificacionRol)
class ConfiguracionNotificacionRolAdmin(admin.ModelAdmin):
    list_display = ('rol', 'tipo_notificacion', 'activo', 'fecha_modificacion')
    list_filter = ('activo', 'tipo_notificacion__categoria', 'fecha_modificacion')
    search_fields = ('rol__nombre', 'tipo_notificacion__nombre', 'tipo_notificacion__codigo')
    ordering = ('rol', 'tipo_notificacion')
    
    fieldsets = (
        ('Configuración', {
            'fields': ('rol', 'tipo_notificacion', 'activo')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
