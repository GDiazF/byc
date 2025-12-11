"""
Configuración del panel de administración de Django para la app maquinarias.

Este archivo registra todos los modelos de la app en el panel de administración de Django,
permitiendo gestionar los datos directamente desde la interfaz web del admin.
Cada modelo tiene su propia clase Admin que personaliza cómo se muestra y gestiona en el admin.
"""

from django.contrib import admin
from .models import (
    TipoEquipo, MarcaEquipo, ModeloEquipo, Equipo,
    Seccion, TipoReparacion, PautaMantenimientoPreventivo, ItemPauta,
    TipoDocumentoMaquinaria, DocumentoMaquinaria, HistorialDocumentoMaquinaria,
    TipoMantenimiento, EstadoOT, EstadoEquipo,
    EstadoCalendarioEquipo, EstadoFuenteEquipo, EstadoManualEquipo,
    OrdenTrabajo, ItemSeccionOT, HistorialObservacionesOT, HistorialOT
)


# ==================== MODELOS DE EQUIPOS ====================
# Estas clases configuran cómo se muestran y gestionan los modelos relacionados con equipos
# en el panel de administración de Django

@admin.register(TipoEquipo)
class TipoEquipoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo TipoEquipo.
    
    TipoEquipo representa las categorías de equipos (ej: Grúa Torre, Excavadora, Camión).
    Esta configuración personaliza cómo se muestra y busca en el panel de administración.
    """
    # Campos que se muestran en la lista de objetos del admin
    # Estos campos aparecen como columnas en la tabla principal
    list_display = ('tipoEquipo_id', 'tipoEquipo', 'siglaEquipo')
    
    # Campos por los que se puede buscar usando la barra de búsqueda del admin
    # Django crea automáticamente un campo de búsqueda cuando se especifica esto
    search_fields = ('tipoEquipo', 'siglaEquipo')
    
    # Orden por defecto de los objetos en la lista
    # Los objetos se ordenan alfabéticamente por nombre del tipo
    ordering = ('tipoEquipo',)


@admin.register(MarcaEquipo)
class MarcaEquipoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo MarcaEquipo.
    
    MarcaEquipo representa las marcas de equipos (ej: Caterpillar, Komatsu, Liebherr).
    Esta configuración personaliza cómo se muestra y busca en el panel de administración.
    """
    # Campos que se muestran en la lista de objetos del admin
    list_display = ('marcaEquipo_id', 'marcaEquipo')
    
    # Campos por los que se puede buscar usando la barra de búsqueda del admin
    search_fields = ('marcaEquipo',)
    
    # Orden por defecto de los objetos en la lista (alfabético por nombre de marca)
    ordering = ('marcaEquipo',)


@admin.register(ModeloEquipo)
class ModeloEquipoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo ModeloEquipo.
    
    ModeloEquipo representa los modelos específicos de equipos (ej: CAT 320D, Komatsu PC200).
    Cada modelo pertenece a un tipo y una marca. Esta configuración permite filtrar por tipo y marca.
    """
    # Campos que se muestran en la lista de objetos del admin
    # Se incluyen las relaciones para ver tipo y marca directamente en la lista
    list_display = ('modeloEquipo_id', 'modeloEquipo', 'tipoEquipo_id', 'marcaEquipo_id')
    
    # Filtros laterales en el admin para filtrar por tipo y marca
    # Django crea automáticamente un panel de filtros en el lado derecho
    list_filter = ('tipoEquipo_id', 'marcaEquipo_id')
    
    # Campos por los que se puede buscar usando la barra de búsqueda del admin
    search_fields = ('modeloEquipo',)
    
    # Orden por defecto de los objetos en la lista (alfabético por nombre de modelo)
    ordering = ('modeloEquipo',)


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Equipo.
    
    Equipo representa cada equipo físico individual en el sistema.
    Esta configuración permite gestionar equipos, filtrarlos por estado, empresa y tipo,
    y buscar por nombre, código interno o patente.
    
    IMPORTANTE: nombreEquipo es de solo lectura porque se genera automáticamente
    basado en el modelo y código interno del equipo.
    """
    # Campos que se muestran en la lista de objetos del admin
    # Se incluyen los campos más importantes para identificar rápidamente cada equipo
    list_display = ('equipo_id', 'nombreEquipo', 'modeloEquipo_id', 'empresa_id', 'codigoInterno', 'patente', 'activo')
    
    # Filtros laterales en el admin para filtrar por estado, empresa y tipo
    # Los equipos activos aparecen primero debido al ordenamiento
    list_filter = ('activo', 'empresa_id', 'modeloEquipo_id__tipoEquipo_id')
    
    # Campos por los que se puede buscar usando la barra de búsqueda del admin
    # Permite buscar equipos por nombre, código interno o patente
    search_fields = ('nombreEquipo', 'codigoInterno', 'patente')
    
    # Campos que no se pueden editar directamente en el admin
    # nombreEquipo se genera automáticamente, por lo que es de solo lectura
    readonly_fields = ('nombreEquipo',)
    
    # Orden por defecto: equipos activos primero, luego por nombre
    # El guión (-) antes de 'activo' indica orden descendente (True antes que False)
    ordering = ('-activo', 'nombreEquipo')


# ==================== MODELOS DE MANTENIMIENTO ====================
# Estas clases configuran cómo se muestran y gestionan los modelos relacionados con mantenimiento
# en el panel de administración de Django

@admin.register(Seccion)
class SeccionAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Seccion.
    
    Seccion representa las partes o sistemas de un equipo (ej: Motor, Sistema Hidráulico, Radiador).
    Cada sección puede tener múltiples tipos de reparación asociados.
    """
    # Campos que se muestran en la lista de objetos del admin
    # total_tipos_reparacion es un método personalizado que cuenta los tipos de reparación
    list_display = ('seccion_id', 'nombre', 'descripcion', 'total_tipos_reparacion')
    
    # Campos por los que se puede buscar usando la barra de búsqueda del admin
    search_fields = ('nombre', 'descripcion')
    
    # Orden por defecto de los objetos en la lista (alfabético por nombre)
    ordering = ('nombre',)
    
    def total_tipos_reparacion(self, obj):
        """
        Método personalizado que cuenta cuántos tipos de reparación tiene asociada esta sección.
        
        Este método se muestra como una columna adicional en la lista del admin.
        Parámetros:
            obj: Instancia del modelo Seccion
        
        Retorna:
            int: Cantidad de tipos de reparación asociados a esta sección
        """
        return obj.tipos_reparacion.count()  # Contar los tipos de reparación relacionados
    
    # Personalizar el título de la columna en el admin
    # Sin esto, Django usaría el nombre del método como título
    total_tipos_reparacion.short_description = 'Tipos de Reparación'


@admin.register(TipoReparacion)
class TipoReparacionAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo TipoReparacion.
    
    TipoReparacion representa los tipos específicos de reparaciones que se pueden realizar
    en una sección de equipo (ej: Cambio de aceite, Reemplazo de filtro, Ajuste de válvulas).
    Cada tipo de reparación pertenece a una sección específica.
    """
    # Campos que se muestran en la lista de objetos del admin
    # Se incluye la sección para identificar rápidamente a qué parte del equipo pertenece
    list_display = ('tipoReparacion_id', 'nombre', 'seccion_id', 'descripcion')
    
    # Filtros laterales en el admin para filtrar por sección
    # Permite ver todos los tipos de reparación de una sección específica
    list_filter = ('seccion_id',)
    
    # Campos por los que se puede buscar usando la barra de búsqueda del admin
    search_fields = ('nombre', 'descripcion')
    
    # Orden por defecto: primero por sección, luego alfabéticamente por nombre
    # Esto agrupa los tipos de reparación por sección
    ordering = ('seccion_id', 'nombre')


class ItemPautaInline(admin.TabularInline):
    """
    Configuración inline para editar items de pauta directamente desde la pauta.
    
    Esta clase permite agregar, editar y eliminar items de pauta (secciones y tipos de reparación)
    directamente desde el formulario de edición de la pauta, sin tener que ir a otra página.
    """
    model = ItemPauta  # Modelo que se edita inline
    extra = 1  # Cantidad de formularios vacíos adicionales que se muestran por defecto
    filter_horizontal = ('tipos_reparacion',)  # Widget especial para seleccionar múltiples tipos de reparación


@admin.register(PautaMantenimientoPreventivo)
class PautaMantenimientoPreventivoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo PautaMantenimientoPreventivo.
    
    PautaMantenimientoPreventivo representa las pautas de mantenimiento preventivo
    que se deben realizar en un modelo específico de equipo.
    Cada pauta contiene múltiples items (secciones y tipos de reparación).
    """
    # Campos que se muestran en la lista de objetos del admin
    # Se incluyen fechas de creación y modificación para auditoría
    list_display = ('pauta_id', 'nombre', 'modeloEquipo_id', 'activo', 'fecha_creacion', 'fecha_modificacion')
    
    # Filtros laterales en el admin para filtrar por estado, tipo de equipo y fecha
    list_filter = ('activo', 'modeloEquipo_id__tipoEquipo_id', 'fecha_creacion')
    
    # Campos por los que se puede buscar usando la barra de búsqueda del admin
    search_fields = ('nombre', 'descripcion')
    
    # Campos que no se pueden editar directamente (se generan automáticamente)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    
    # Orden por defecto: pautas activas primero, luego por nombre
    ordering = ('-activo', 'nombre')
    
    # Inlines: permite editar items de pauta directamente desde la pauta
    inlines = [ItemPautaInline]
    
    # Agrupar campos en secciones colapsables para mejor organización
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'modeloEquipo_id', 'descripcion', 'activo')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)  # Esta sección está colapsada por defecto
        }),
    )


@admin.register(ItemPauta)
class ItemPautaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo ItemPauta.
    
    ItemPauta representa un item individual dentro de una pauta de mantenimiento.
    Cada item asocia una sección con múltiples tipos de reparación que deben realizarse.
    """
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
    """
    Configuración del admin para el modelo TipoDocumentoMaquinaria.
    
    TipoDocumentoMaquinaria representa los tipos de documentos que pueden asociarse
    a equipos (ej: Permiso de Circulación, Seguro, Certificado de Inspección).
    """
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
    """
    Configuración del admin para el modelo DocumentoMaquinaria.
    
    DocumentoMaquinaria representa los documentos físicos asociados a equipos.
    Cada documento tiene un archivo, fecha de vencimiento (si aplica) y estado.
    """
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
        """
        Método personalizado que determina el estado del documento según su fecha de vencimiento.
        
        Args:
            obj: Instancia del modelo DocumentoMaquinaria.
            
        Returns:
            str: Estado del documento ('Vencido', 'Por vencer', o 'Vigente').
        """
        if obj.esta_vencido:
            return 'Vencido'
        elif obj.esta_por_vencer:
            return 'Por vencer'
        else:
            return 'Vigente'
    estado_documento.short_description = 'Estado'


@admin.register(HistorialDocumentoMaquinaria)
class HistorialDocumentoMaquinariaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo HistorialDocumentoMaquinaria.
    
    HistorialDocumentoMaquinaria almacena documentos que fueron reemplazados o eliminados.
    Permite mantener un registro histórico de todos los documentos que ha tenido un equipo.
    """
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
    """
    Configuración del admin para el modelo TipoMantenimiento.
    
    TipoMantenimiento representa los tipos de mantenimiento que se pueden realizar
    en equipos (ej: Preventivo, Correctivo, Predictivo).
    """
    list_display = ('tipoMantenimiento_id', 'nombre', 'descripcion', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)


@admin.register(EstadoOT)
class EstadoOTAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo EstadoOT.
    
    EstadoOT representa los estados posibles de una orden de trabajo
    (ej: Pendiente, En Proceso, Completada, Cancelada).
    """
    list_display = ('estadoOT_id', 'nombre', 'color', 'orden', 'activo')
    list_filter = ('activo', 'color')
    search_fields = ('nombre', 'descripcion')
    ordering = ('orden', 'nombre')


@admin.register(EstadoEquipo)
class EstadoEquipoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo EstadoEquipo.
    
    EstadoEquipo representa los estados posibles de un equipo
    (ej: Operativo, En Mantenimiento, Fuera de Servicio).
    """
    list_display = ('estadoEquipo_id', 'nombre', 'color', 'orden', 'activo')
    list_filter = ('activo', 'color')
    search_fields = ('nombre', 'descripcion')
    ordering = ('orden', 'nombre')


# ==================== MODELOS DE ESTADOS CALENDARIO ====================

@admin.register(EstadoCalendarioEquipo)
class EstadoCalendarioEquipoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo EstadoCalendarioEquipo.
    
    EstadoCalendarioEquipo representa los estados que se muestran en el calendario
    de maquinarias. Cada estado tiene colores, prioridad y puede ser bloqueante.
    """
    list_display = ('nombre', 'nombre_corto', 'color', 'background_color', 'prioridad', 'es_bloqueante', 'es_predeterminado', 'activo')
    list_filter = ('activo', 'es_bloqueante', 'es_predeterminado')
    search_fields = ('nombre', 'nombre_corto')
    ordering = ('-activo', '-prioridad', 'nombre')
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'nombre_corto', 'activo')
        }),
        ('Colores', {
            'fields': ('color', 'background_color')
        }),
        ('Configuración', {
            'fields': ('prioridad', 'es_bloqueante', 'es_predeterminado')
        }),
    )


@admin.register(EstadoFuenteEquipo)
class EstadoFuenteEquipoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo EstadoFuenteEquipo.
    
    EstadoFuenteEquipo mapea estados de calendario con estados de equipo,
    permitiendo determinar qué estado mostrar en el calendario según el estado del equipo.
    """
    list_display = ('estado_calendario', 'estado_equipo', 'filtro_extra')
    list_filter = ('estado_calendario', 'estado_equipo')
    search_fields = ('estado_calendario__nombre', 'estado_equipo__nombre')
    ordering = ('estado_calendario', 'estado_equipo')


@admin.register(EstadoManualEquipo)
class EstadoManualEquipoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo EstadoManualEquipo.
    
    EstadoManualEquipo permite asignar estados temporales a equipos independientemente
    de las órdenes de trabajo o asignaciones a faenas.
    """
    list_display = ('equipo', 'estado', 'fecha_inicio', 'fecha_fin', 'fecha_creacion')
    list_filter = ('estado', 'fecha_inicio', 'fecha_fin')
    search_fields = ('equipo__nombreEquipo', 'estado__nombre', 'observaciones')
    date_hierarchy = 'fecha_inicio'
    ordering = ('-fecha_creacion',)


# ==================== MODELOS DE ORDEN DE TRABAJO ====================

class ItemSeccionOTInline(admin.TabularInline):
    """
    Configuración inline para editar items de sección de OT directamente desde la OT.
    
    Permite agregar, editar y eliminar items de sección (secciones y tipos de reparación)
    directamente desde el formulario de edición de la orden de trabajo.
    """
    model = ItemSeccionOT
    extra = 0
    filter_horizontal = ('tipos_reparacion',)
    fields = ('seccion_id', 'tipos_reparacion', 'estado_seccion_id')
    readonly_fields = ()


class HistorialObservacionesOTInline(admin.TabularInline):
    """
    Configuración inline para ver el historial de observaciones de una OT.
    
    Muestra todas las observaciones agregadas a la orden de trabajo en orden cronológico.
    Las observaciones no se pueden eliminar desde aquí (solo lectura).
    """
    model = HistorialObservacionesOT
    extra = 0
    fields = ('observacion', 'usuario', 'fecha')
    readonly_fields = ('fecha',)
    can_delete = False


@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo OrdenTrabajo.
    
    OrdenTrabajo representa las órdenes de trabajo para mantenimiento de equipos.
    Cada OT incluye información del equipo, personal asignado, secciones a reparar,
    y un historial de observaciones y cambios de estado.
    """
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
        """
        Método personalizado para eliminar una orden de trabajo y sus objetos relacionados.
        
        Este método se ejecuta cuando se elimina una OT individual desde el admin.
        Elimina manualmente los objetos relacionados (historial, items de sección, observaciones)
        antes de eliminar la OT para evitar problemas de permisos y mantener la integridad de datos.
        
        Parámetros:
            request: Objeto HttpRequest de Django
            obj: Instancia de OrdenTrabajo a eliminar
        """
        # Paso 1: Eliminar objetos relacionados manualmente antes de eliminar la OT
        # Esto evita problemas de permisos y asegura que todo se elimine correctamente
        obj.historial.all().delete()  # Eliminar todos los registros de HistorialOT relacionados
        obj.items_secciones.all().delete()  # Eliminar todos los ItemSeccionOT relacionados
        obj.historial_observaciones.all().delete()  # Eliminar todas las HistorialObservacionesOT relacionadas
        
        # Paso 2: Eliminar la OT principal
        # Ahora que los objetos relacionados están eliminados, se puede eliminar la OT
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        """
        Método personalizado para eliminar múltiples órdenes de trabajo y sus objetos relacionados.
        
        Este método se ejecuta cuando se eliminan múltiples OTs desde el admin (acción masiva).
        Usa una transacción atómica para asegurar que todas las eliminaciones se completen
        o se reviertan todas si hay un error.
        
        Parámetros:
            request: Objeto HttpRequest de Django
            queryset: QuerySet con las OTs a eliminar
        """
        from django.db import transaction
        
        # Usar transacción atómica para asegurar integridad de datos
        # Si falla la eliminación de alguna OT, se revierten todos los cambios
        with transaction.atomic():
            # Paso 1: Para cada OT en el queryset, eliminar sus objetos relacionados
            for obj in queryset:
                # Eliminar objetos relacionados manualmente para evitar problemas de permisos
                obj.historial.all().delete()  # Eliminar HistorialOT relacionado
                obj.items_secciones.all().delete()  # Eliminar ItemSeccionOT relacionado
                obj.historial_observaciones.all().delete()  # Eliminar HistorialObservacionesOT relacionado
            
            # Paso 2: Eliminar todas las OTs del queryset
            # Esto se hace después de eliminar todos los objetos relacionados
            queryset.delete()


@admin.register(ItemSeccionOT)
class ItemSeccionOTAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo ItemSeccionOT.
    
    ItemSeccionOT representa una sección específica dentro de una orden de trabajo,
    asociada con múltiples tipos de reparación que deben realizarse en esa sección.
    """
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
    """
    Configuración del admin para el modelo HistorialObservacionesOT.
    
    HistorialObservacionesOT almacena todas las observaciones agregadas a una orden de trabajo,
    incluyendo quién las agregó y cuándo, para mantener un registro completo de cambios.
    """
    list_display = ('historial_id', 'ot_id', 'usuario', 'fecha', 'observacion_preview')
    list_filter = ('ot_id', 'usuario', 'fecha')
    search_fields = ('ot_id__folio', 'observacion')
    readonly_fields = ('fecha',)
    ordering = ('-fecha',)
    
    def observacion_preview(self, obj):
        """
        Método personalizado que muestra una vista previa de la observación.
        
        Si la observación es muy larga, la trunca a 100 caracteres y agrega '...'.
        
        Args:
            obj: Instancia del modelo HistorialObservacionesOT.
            
        Returns:
            str: Observación completa o truncada a 100 caracteres.
        """
        return obj.observacion[:100] + '...' if len(obj.observacion) > 100 else obj.observacion
    observacion_preview.short_description = 'Observación'


@admin.register(HistorialOT)
class HistorialOTAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo HistorialOT.
    
    HistorialOT almacena todos los cambios realizados en órdenes de trabajo,
    incluyendo quién hizo el cambio, cuándo y qué datos cambiaron.
    """
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
        """
        Método personalizado que muestra una vista previa de la descripción.
        
        Si la descripción es muy larga, la trunca a 80 caracteres y agrega '...'.
        
        Args:
            obj: Instancia del modelo HistorialOT.
            
        Returns:
            str: Descripción completa o truncada a 80 caracteres, o '-' si no hay descripción.
        """
        if obj.descripcion:
            return obj.descripcion[:80] + "..." if len(obj.descripcion) > 80 else obj.descripcion
        return "-"
    descripcion_corta.short_description = "Descripción"
    
    def has_add_permission(self, request):
        """
        No permite crear manualmente registros de historial desde el admin.
        
        Los registros de historial se crean automáticamente mediante signals cuando
        se realizan cambios en las órdenes de trabajo.
        
        Args:
            request: Objeto HttpRequest de Django.
            
        Returns:
            bool: Siempre False, no se pueden crear manualmente.
        """
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Permite eliminación solo si el usuario es superuser.
        
        En producción, esto debería ser False para mantener la integridad de auditoría,
        pero se permite para pruebas y limpieza de datos.
        
        Args:
            request: Objeto HttpRequest de Django.
            obj: Instancia del modelo (opcional).
            
        Returns:
            bool: True solo si el usuario es superuser, False en caso contrario.
        """
        return request.user.is_superuser
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ot', 'usuario')
