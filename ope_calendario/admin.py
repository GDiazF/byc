from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Estado, EstadoFuente, Turno, TurnoBloque, Faena, AsignacionFaena, EstadoManual, HistorialFaena
)

# ============================================================================
# ADMIN PARA MODELOS DE CALENDARIO
# ============================================================================

@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Estado.
    Permite gestionar los estados dinámicos del sistema de calendario.
    """
    # Campos a mostrar en la lista del admin
    list_display = ['nombre', 'nombre_corto', 'color_preview', 'background_color_preview', 'prioridad', 'es_bloqueante', 'es_predeterminado', 'activo']
    
    # Filtros disponibles en el panel lateral
    list_filter = ['activo', 'es_bloqueante', 'es_predeterminado', 'prioridad']
    
    # Campos por los que se puede buscar
    search_fields = ['nombre', 'nombre_corto']
    
    # Ordenamiento por defecto: activos primero, luego por prioridad descendente, luego por nombre
    ordering = ['-activo', '-prioridad', 'nombre']
    
    # Agrupación de campos en el formulario de edición
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
        """
        Muestra una vista previa del color de texto del estado.
        Crea un div con el color como fondo para visualización rápida.
        
        Parámetros:
            obj: Instancia de Estado
        
        Retorna:
            str: HTML con un div coloreado o "-" si no hay color
        """
        if obj.color:
            return format_html(
                '<div style="background-color: {}; width: 30px; height: 20px; border: 1px solid #ccc; border-radius: 3px;"></div>',
                obj.color
            )
        return "-"
    color_preview.short_description = "Color Texto"
    
    def background_color_preview(self, obj):
        """
        Muestra una vista previa del color de fondo del estado.
        Crea un div con el color de fondo para visualización rápida.
        
        Parámetros:
            obj: Instancia de Estado
        
        Retorna:
            str: HTML con un div coloreado o "-" si no hay color de fondo
        """
        if obj.background_color:
            return format_html(
                '<div style="background-color: {}; width: 30px; height: 20px; border: 1px solid #ccc; border-radius: 3px;"></div>',
                obj.background_color
            )
        return "-"
    background_color_preview.short_description = "Color Fondo"

@admin.register(EstadoFuente)
class EstadoFuenteAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo EstadoFuente.
    Permite gestionar las fuentes externas de estados (mapeo de estados a otros modelos).
    """
    # Campos a mostrar en la lista del admin
    list_display = ['estado', 'content_type', 'campo_fecha_inicio', 'campo_fecha_fin', 'campo_personal']
    
    # Filtros disponibles en el panel lateral
    list_filter = ['estado__activo', 'content_type']
    
    # Campos por los que se puede buscar
    search_fields = ['estado__nombre']
    
    # Ordenamiento por defecto: por nombre del estado
    ordering = ['estado__nombre']
    
    # Agrupación de campos en el formulario de edición
    fieldsets = (
        ('Estado Asociado', {
            'fields': ('estado',)
        }),
        ('Configuración de Fuente', {
            'fields': ('content_type', 'campo_fecha_inicio', 'campo_fecha_fin', 'campo_personal')
        }),
    )

class TurnoBloqueInline(admin.TabularInline):
    """
    Inline admin para gestionar bloques de turno directamente desde el formulario de Turno.
    Permite agregar, editar y eliminar bloques sin salir del formulario del turno.
    """
    model = TurnoBloque
    extra = 1  # Mostrar 1 formulario vacío adicional por defecto
    ordering = ['orden']  # Ordenar por orden ascendente
    fields = ['orden', 'duracion_dias', 'estado']  # Campos a mostrar en el inline

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Turno.
    Permite gestionar los turnos del sistema con sus bloques asociados.
    """
    # Campos a mostrar en la lista del admin
    list_display = ['nombre', 'longitud_ciclo', 'activo', 'descripcion_short', 'cantidad_bloques']
    
    # Filtros disponibles en el panel lateral
    list_filter = ['activo']
    
    # Campos por los que se puede buscar
    search_fields = ['nombre', 'descripcion']
    
    # Ordenamiento por defecto: por nombre
    ordering = ['nombre']
    
    # Inlines: permite gestionar bloques desde el formulario del turno
    inlines = [TurnoBloqueInline]
    
    # Agrupación de campos en el formulario de edición
    fieldsets = (
        ('Información del Turno', {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
    )
    
    def descripcion_short(self, obj):
        """
        Muestra una versión corta de la descripción del turno (máximo 50 caracteres).
        
        Parámetros:
            obj: Instancia de Turno
        
        Retorna:
            str: Descripción truncada con "..." o "-" si no hay descripción
        """
        if obj.descripcion:
            return obj.descripcion[:50] + "..." if len(obj.descripcion) > 50 else obj.descripcion
        return "-"
    descripcion_short.short_description = "Descripción"
    
    def cantidad_bloques(self, obj):
        """
        Muestra la cantidad de bloques que tiene el turno con formato visual.
        
        Parámetros:
            obj: Instancia de Turno
        
        Retorna:
            str: HTML con badge mostrando la cantidad de bloques
        """
        count = obj.bloques.count()
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-weight: bold;">{} bloque{}</span>',
            count, 's' if count != 1 else ''
        )
    cantidad_bloques.short_description = "Bloques"

@admin.register(TurnoBloque)
class TurnoBloqueAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo TurnoBloque.
    Permite gestionar los bloques individuales que componen un turno.
    """
    # Campos a mostrar en la lista del admin
    list_display = ['turno', 'orden', 'duracion_dias', 'estado', 'estado_color_preview']
    
    # Filtros disponibles en el panel lateral
    list_filter = ['turno', 'estado', 'estado__activo']
    
    # Ordenamiento por defecto: por turno y luego por orden
    ordering = ['turno', 'orden']
    
    # Campos por los que se puede buscar
    search_fields = ['turno__nombre', 'estado__nombre']
    
    # Agrupación de campos en el formulario de edición
    fieldsets = (
        ('Información del Bloque', {
            'fields': ('turno', 'orden', 'duracion_dias')
        }),
        ('Estado Asociado', {
            'fields': ('estado',)
        }),
    )
    
    def estado_color_preview(self, obj):
        """
        Muestra una vista previa del estado asociado con sus colores.
        Crea un badge con el color de fondo y texto del estado.
        
        Parámetros:
            obj: Instancia de TurnoBloque
        
        Retorna:
            str: HTML con badge coloreado o nombre del estado si no hay colores
        """
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
    """
    Configuración del admin para el modelo Faena.
    Permite gestionar las faenas del sistema con información de asignaciones.
    """
    # Campos a mostrar en la lista del admin
    list_display = ['nombre', 'ubicacion', 'activo', 'descripcion_short', 'asignaciones_count']
    
    # Filtros disponibles en el panel lateral
    list_filter = ['activo']
    
    # Campos por los que se puede buscar
    search_fields = ['nombre', 'ubicacion', 'descripcion']
    
    # Ordenamiento por defecto: por nombre
    ordering = ['nombre']
    
    # Agrupación de campos en el formulario de edición
    fieldsets = (
        ('Información de la Faena', {
            'fields': ('codigo', 'nombre', 'ubicacion', 'descripcion', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
    )
    
    def get_deleted_objects(self, objs, request):
        """
        Sobrescribe el método para permitir eliminación en cascada sin verificar permisos
        para objetos relacionados cuando el usuario es superusuario.
        """
        from django.contrib.admin.utils import NestedObjects
        from django.db import router
        
        # Usar el collector de Django para obtener objetos relacionados
        collector = NestedObjects(using=router.db_for_write(objs[0]))
        collector.collect(objs)
        
        # Si el usuario es superusuario, permitir eliminar todos los objetos relacionados
        # sin verificar permisos individuales
        if request.user.is_superuser:
            # Retornar los objetos a eliminar sin verificar permisos
            to_delete = collector.nested()
            protected = []
            model_count = {model._meta.verbose_name_plural: len(objs) for model, objs in collector.model_objs.items()}
            return to_delete, model_count, protected, collector.perms_lacking
        
        # Para usuarios no superusuarios, usar el comportamiento por defecto
        return super().get_deleted_objects(objs, request)
    
    def descripcion_short(self, obj):
        """
        Muestra una versión corta de la descripción de la faena (máximo 50 caracteres).
        
        Parámetros:
            obj: Instancia de Faena
        
        Retorna:
            str: Descripción truncada con "..." o "-" si no hay descripción
        """
        if obj.descripcion:
            return obj.descripcion[:50] + "..." if len(obj.descripcion) > 50 else obj.descripcion
        return "-"
    descripcion_short.short_description = "Descripción"
    
    def asignaciones_count(self, obj):
        """
        Muestra la cantidad de asignaciones activas de personal a la faena.
        Usa colores diferentes según si hay asignaciones o no.
        
        Parámetros:
            obj: Instancia de Faena
        
        Retorna:
            str: HTML con badge mostrando la cantidad de asignaciones activas
        """
        try:
            if obj.pk:
                # Usar el related_name correcto: 'asignaciones' según el modelo AsignacionFaena
                count = obj.asignaciones.filter(activo=True).count()
                color = '#27ae60' if count > 0 else '#95a5a6'  # Verde si hay asignaciones, gris si no
                return format_html(
                    '<span style="background-color: {}; color: white; padding: 2px 8px; '
                    'border-radius: 3px; font-weight: bold;">{} asignación{}</span>',
                    color, count, 'es' if count != 1 else ''
                )
            return format_html('<span style="color: #95a5a6;">-</span>')
        except Exception as e:
            return format_html('<span style="color: red;">Error</span>')
    asignaciones_count.short_description = "Asignaciones Activas"

@admin.register(AsignacionFaena)
class AsignacionFaenaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo AsignacionFaena.
    Permite gestionar las asignaciones de personal a faenas con sus turnos.
    """
    # Campos a mostrar en la lista del admin
    list_display = [
        'personal', 'faena', 'turno', 'fecha_inicio', 'fecha_fin', 
        'bloque_inicio', 'duracion_dias', 'activo', 'tiene_observaciones'
    ]
    
    # Filtros disponibles en el panel lateral
    list_filter = ['activo', 'faena', 'turno', 'fecha_inicio', 'fecha_fin']
    
    # Campos por los que se puede buscar
    search_fields = ['personal__nombre', 'personal__apepat', 'faena__nombre', 'turno__nombre', 'observaciones']
    
    # Jerarquía de fechas para navegación rápida
    date_hierarchy = 'fecha_inicio'
    
    # Ordenamiento por defecto: por personal y luego por fecha de inicio descendente
    ordering = ['personal', '-fecha_inicio']
    
    # Agrupación de campos en el formulario de edición
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
            'classes': ('collapse',)  # Colapsado por defecto
        }),
    )
    
    def duracion_dias(self, obj):
        """
        Calcula y muestra la duración de la asignación en días.
        Incluye tanto el día de inicio como el día de fin en el cálculo.
        
        Parámetros:
            obj: Instancia de AsignacionFaena
        
        Retorna:
            str: Duración en días o mensaje si no hay fechas
        """
        if obj.fecha_inicio and obj.fecha_fin:
            delta = obj.fecha_fin - obj.fecha_inicio
            dias = delta.days + 1  # +1 para incluir ambos días
            return f"{dias} día{'s' if dias != 1 else ''}"
        elif obj.fecha_inicio:
            return "Sin fecha fin"
        return "-"
    duracion_dias.short_description = "Duración"
    
    def tiene_observaciones(self, obj):
        """
        Indica si la asignación tiene observaciones con un icono visual.
        Muestra un tooltip con las observaciones al pasar el mouse.
        
        Parámetros:
            obj: Instancia de AsignacionFaena
        
        Retorna:
            str: HTML con icono y tooltip o "-" si no hay observaciones
        """
        if obj.observaciones:
            return format_html(
                '<span style="color: #3498db;" title="{}">📝 Sí</span>',
                obj.observaciones[:100] + "..." if len(obj.observaciones) > 100 else obj.observaciones
            )
        return format_html('<span style="color: #95a5a6;">-</span>')
    tiene_observaciones.short_description = "Observaciones"
    
    def get_queryset(self, request):
        """
        Optimiza las consultas usando select_related para evitar N+1 queries.
        
        Parámetros:
            request: HttpRequest
        
        Retorna:
            QuerySet: QuerySet optimizado con relaciones precargadas
        """
        return super().get_queryset(request).select_related('personal', 'faena', 'turno', 'bloque_inicio')

@admin.register(EstadoManual)
class EstadoManualAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo EstadoManual.
    Permite gestionar los estados manuales asignados al personal.
    """
    # Campos a mostrar en la lista del admin
    list_display = [
        'personal', 'estado', 'fecha_inicio', 'fecha_fin', 
        'duracion_dias', 'motivo_short', 'activo', 'creado_en'
    ]
    
    # Filtros disponibles en el panel lateral
    list_filter = ['activo', 'estado', 'fecha_inicio', 'fecha_fin', 'creado_en']
    
    # Campos por los que se puede buscar
    search_fields = ['personal__nombre', 'personal__apepat', 'personal__apemat', 'motivo']
    
    # Jerarquía de fechas para navegación rápida
    date_hierarchy = 'fecha_inicio'
    
    # Ordenamiento por defecto: más recientes primero, luego por personal
    ordering = ['-creado_en', 'personal']
    
    # Campos de solo lectura (no editables)
    readonly_fields = ['creado_en']
    
    # Agrupación de campos en el formulario de edición
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
            'classes': ('collapse',)  # Colapsado por defecto
        }),
    )
    
    def duracion_dias(self, obj):
        """
        Calcula y muestra la duración del estado manual en días.
        Incluye tanto el día de inicio como el día de fin en el cálculo.
        
        Parámetros:
            obj: Instancia de EstadoManual
        
        Retorna:
            str: HTML con duración en días o mensaje si no hay fechas
        """
        if obj.fecha_inicio and obj.fecha_fin:
            delta = obj.fecha_fin - obj.fecha_inicio
            dias = delta.days + 1  # +1 para incluir ambos días
            return format_html(
                '<span style="font-weight: bold;">{} día{}</span>',
                dias, 's' if dias != 1 else ''
            )
        elif obj.fecha_inicio:
            return "Sin fecha fin"
        return "-"
    duracion_dias.short_description = "Duración"
    
    def motivo_short(self, obj):
        """
        Muestra una versión corta del motivo (máximo 50 caracteres).
        
        Parámetros:
            obj: Instancia de EstadoManual
        
        Retorna:
            str: Motivo truncado con "..." o "-" si no hay motivo
        """
        if obj.motivo:
            return obj.motivo[:50] + "..." if len(obj.motivo) > 50 else obj.motivo
        return "-"
    motivo_short.short_description = "Motivo"
    
    def get_queryset(self, request):
        """
        Optimiza las consultas usando select_related para evitar N+1 queries.
        
        Parámetros:
            request: HttpRequest
        
        Retorna:
            QuerySet: QuerySet optimizado con relaciones precargadas
        """
        return super().get_queryset(request).select_related('personal', 'estado')

@admin.register(HistorialFaena)
class HistorialFaenaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo HistorialFaena.
    Permite visualizar el historial de cambios de faenas (solo lectura).
    El historial se crea automáticamente mediante señales Django.
    """
    # Campos a mostrar en la lista del admin
    list_display = ['faena', 'fecha_hora', 'accion', 'usuario', 'personal', 'descripcion_corta']
    
    # Filtros disponibles en el panel lateral
    list_filter = ['accion', 'fecha_hora', 'faena']
    
    # Campos por los que se puede buscar
    search_fields = ['faena__codigo', 'faena__nombre', 'descripcion', 'personal__nombre', 'personal__apepat']
    
    # Jerarquía de fechas para navegación rápida
    date_hierarchy = 'fecha_hora'
    
    # Ordenamiento por defecto: más recientes primero
    ordering = ['-fecha_hora']
    
    # Todos los campos son de solo lectura (auditoría)
    readonly_fields = ['fecha_hora', 'faena', 'usuario', 'accion', 'personal', 'descripcion', 'datos_previos', 'datos_nuevos']
    
    # Agrupación de campos en el formulario de edición
    fieldsets = (
        ('Información del Registro', {
            'fields': ('faena', 'fecha_hora', 'usuario', 'accion')
        }),
        ('Detalles', {
            'fields': ('personal', 'descripcion')
        }),
        ('Datos Técnicos', {
            'fields': ('datos_previos', 'datos_nuevos'),
            'classes': ('collapse',)  # Colapsado por defecto
        }),
    )
    
    def descripcion_corta(self, obj):
        """
        Muestra una versión corta de la descripción (máximo 80 caracteres).
        
        Parámetros:
            obj: Instancia de HistorialFaena
        
        Retorna:
            str: Descripción truncada con "..." o "-" si no hay descripción
        """
        if obj.descripcion:
            return obj.descripcion[:80] + "..." if len(obj.descripcion) > 80 else obj.descripcion
        return "-"
    descripcion_corta.short_description = "Descripción"
    
    def has_add_permission(self, request):
        """
        No permite crear registros manualmente desde el admin.
        El historial se crea automáticamente mediante señales Django.
        
        Parámetros:
            request: HttpRequest
        
        Retorna:
            bool: Siempre False (no permitir creación manual)
        """
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        No permite modificar registros del historial.
        El historial es de solo lectura para mantener la integridad de la auditoría.
        
        Parámetros:
            request: HttpRequest
            obj: Instancia de HistorialFaena (opcional)
        
        Retorna:
            bool: Siempre False (no permitir modificación)
        """
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Permite eliminar registros del historial solo para superusuarios.
        Esto es necesario para permitir la eliminación en cascada cuando se elimina una Faena.
        
        Parámetros:
            request: HttpRequest
            obj: Instancia de HistorialFaena (opcional)
        
        Retorna:
            bool: True si el usuario es superusuario, False en caso contrario
        """
        return request.user.is_superuser
    
    def get_queryset(self, request):
        """
        Optimiza las consultas usando select_related para evitar N+1 queries.
        
        Parámetros:
            request: HttpRequest
        
        Retorna:
            QuerySet: QuerySet optimizado con relaciones precargadas
        """
        return super().get_queryset(request).select_related('faena', 'usuario', 'personal')

# ============================================================================
# PERSONALIZACIÓN DEL SITE ADMIN
# ============================================================================
# Configuración personalizada del sitio de administración de Django.
# Define los títulos y encabezados que se muestran en el admin.

admin.site.site_header = "Administración del Calendario de Planificación"
admin.site.site_title = "Calendario Admin"
admin.site.index_title = "Panel de Control del Calendario"
