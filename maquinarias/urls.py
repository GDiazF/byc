from django.urls import path
from . import views

# Nombre de la aplicación para namespacing de URLs
# Permite usar 'maquinarias:nombre_vista' en templates y código
app_name = 'maquinarias'

# Configuración de rutas URL para la aplicación de maquinarias
# Las rutas están organizadas por funcionalidad para facilitar el mantenimiento
urlpatterns = [
    # ============================================================================
    # VISTAS PRINCIPALES DE EQUIPOS
    # ============================================================================
    # Estas rutas renderizan páginas HTML completas para la gestión de equipos
    path('equipos/', views.lista_equipos, name='lista_equipos'),  # Lista principal de equipos activos
    path('equipos/desactivados/', views.equipos_desactivados, name='equipos_desactivados'),  # Lista de equipos desactivados
    path('equipos/crear/', views.crear_equipo, name='crear_equipo'),  # Formulario para crear nuevo equipo
    path('equipos/<int:equipo_id>/editar/', views.editar_equipo, name='editar_equipo'),  # Formulario para editar equipo existente
    path('equipos/<int:equipo_id>/documentacion/', views.documentacion_equipo, name='documentacion_equipo'),  # Gestión de documentación del equipo
    
    # ============================================================================
    # APIs PARA DOCUMENTACIÓN DE MAQUINARIAS
    # ============================================================================
    # Estas rutas manejan operaciones AJAX relacionadas con documentos de equipos
    path('api/tipos-documentos/', views.api_tipos_documentos_maquinaria, name='api_tipos_documentos_maquinaria'),  # Listar tipos de documentos disponibles
    path('api/equipos/<int:equipo_id>/documentos/', views.api_documentos_equipo, name='api_documentos_equipo'),  # Listar documentos de un equipo
    path('api/equipos/<int:equipo_id>/documentos/subir/', views.api_subir_documento_maquinaria, name='api_subir_documento_maquinaria'),  # Subir nuevo documento
    path('api/documentos/<int:documento_id>/eliminar/', views.api_eliminar_documento_maquinaria, name='api_eliminar_documento_maquinaria'),  # Eliminar documento (mueve a historial)
    path('api/equipos/<int:equipo_id>/documentos/historial/', views.api_historial_documentos_equipo, name='api_historial_documentos_equipo'),  # Obtener historial de documentos
    
    # ============================================================================
    # APIs PARA CRUD DE EQUIPOS
    # ============================================================================
    # Estas rutas manejan operaciones AJAX para crear, leer, actualizar y eliminar equipos
    path('api/equipos/', views.api_listar_equipos, name='api_listar_equipos'),  # Listar equipos con filtros y paginación
    path('api/equipos/guardar/', views.api_guardar_equipo, name='api_guardar_equipo'),  # Crear o actualizar equipo (unificado)
    path('api/equipos/<int:equipo_id>/eliminar/', views.api_eliminar_equipo, name='api_eliminar_equipo'),  # Eliminar equipo
    path('api/equipos/<int:equipo_id>/toggle-activo/', views.api_toggle_activo_equipo, name='api_toggle_activo_equipo'),  # Activar/desactivar equipo
    
    # ============================================================================
    # APIs PARA OBTENER DATOS DE SELECTS (FILTROS EN CASCADA)
    # ============================================================================
    # Estas rutas proporcionan datos para poblar selects en formularios con filtros en cascada
    path('api/tipos-equipo/', views.api_tipos_equipo, name='api_tipos_equipo'),  # Listar todos los tipos de equipo
    path('api/marcas-equipo/', views.api_marcas_equipo, name='api_marcas_equipo'),  # Listar todas las marcas
    path('api/modelos-equipo/', views.api_modelos_equipo, name='api_modelos_equipo'),  # Listar modelos con filtros opcionales
    
    # ============================================================================
    # VISTAS Y APIs PARA SECCIONES
    # ============================================================================
    # Gestión de secciones de equipos (motor, radiador, sistema hidráulico, etc.)
    path('secciones/', views.lista_secciones, name='lista_secciones'),  # Vista principal de secciones
    path('api/secciones/', views.api_listar_secciones, name='api_listar_secciones'),  # API para listar secciones con paginación
    path('api/secciones/guardar/', views.api_guardar_seccion, name='api_guardar_seccion'),  # API para crear/actualizar sección
    path('api/secciones/<int:seccion_id>/eliminar/', views.api_eliminar_seccion, name='api_eliminar_seccion'),  # API para eliminar sección
    
    # ============================================================================
    # VISTAS Y APIs PARA TIPOS DE REPARACIÓN
    # ============================================================================
    # Gestión de tipos de reparación asociados a secciones
    path('tipos-reparacion/', views.lista_tipos_reparacion, name='lista_tipos_reparacion'),  # Vista principal de tipos de reparación
    path('api/tipos-reparacion/', views.api_listar_tipos_reparacion, name='api_listar_tipos_reparacion'),  # API para listar tipos con paginación
    path('api/tipos-reparacion/guardar/', views.api_guardar_tipo_reparacion, name='api_guardar_tipo_reparacion'),  # API para crear/actualizar tipo
    path('api/tipos-reparacion/<int:tipo_id>/eliminar/', views.api_eliminar_tipo_reparacion, name='api_eliminar_tipo_reparacion'),  # API para eliminar tipo
    
    # ============================================================================
    # VISTAS Y APIs PARA PAUTAS DE MANTENIMIENTO
    # ============================================================================
    # Gestión de pautas de mantenimiento preventivo para modelos de equipos
    path('pautas-mantenimiento/', views.lista_pautas_mantenimiento, name='lista_pautas_mantenimiento'),  # Vista principal de pautas
    path('pautas-mantenimiento/modelo/<int:modelo_id>/', views.ver_pautas_modelo, name='ver_pautas_modelo'),  # Ver todas las pautas de un modelo específico
    path('pautas-mantenimiento/crear/', views.crear_pauta_mantenimiento, name='crear_pauta_mantenimiento'),  # Formulario para crear nueva pauta
    path('pautas-mantenimiento/<int:pauta_id>/editar/', views.editar_pauta_mantenimiento, name='editar_pauta_mantenimiento'),  # Formulario para editar pauta existente
    
    # APIs para operaciones CRUD de pautas
    path('api/pautas-mantenimiento/', views.api_listar_pautas_mantenimiento, name='api_listar_pautas_mantenimiento'),  # Listar todas las pautas con sus modelos
    path('api/pautas-mantenimiento/modelo/<int:modelo_id>/', views.api_pautas_por_modelo, name='api_pautas_por_modelo'),  # Obtener pautas de un modelo específico
    path('api/pautas-mantenimiento/guardar/', views.api_guardar_pauta_mantenimiento, name='api_guardar_pauta_mantenimiento'),  # Crear o actualizar pauta
    path('api/pautas-mantenimiento/<int:pauta_id>/', views.api_detalle_pauta, name='api_detalle_pauta'),  # Obtener detalle completo de una pauta
    path('api/pautas-mantenimiento/<int:pauta_id>/toggle-activo/', views.api_toggle_activo_pauta, name='api_toggle_activo_pauta'),  # Activar/desactivar pauta
    path('api/pautas-mantenimiento/<int:pauta_id>/eliminar/', views.api_eliminar_pauta, name='api_eliminar_pauta'),  # Eliminar pauta
    
    # ============================================================================
    # VISTA DE CALENDARIO DE MAQUINARIAS
    # ============================================================================
    # Vista que muestra un calendario mensual con el estado de los equipos
    path('calendario-maquinarias/', views.calendario_maquinarias, name='calendario_maquinarias'),
    
    # ============================================================================
    # VISTAS PARA ORDEN DE TRABAJO
    # ============================================================================
    # Gestión de órdenes de trabajo para mantenimiento de equipos
    path('ordenes-trabajo/', views.lista_ordenes_trabajo, name='lista_ordenes_trabajo'),  # Lista principal de órdenes de trabajo
    path('ordenes-trabajo/crear/', views.crear_orden_trabajo, name='crear_orden_trabajo'),  # Formulario para crear nueva OT
    path('ordenes-trabajo/<int:ot_id>/editar/', views.editar_orden_trabajo, name='editar_orden_trabajo'),  # Formulario para editar OT existente
    path('ordenes-trabajo/<int:ot_id>/pdf/', views.generar_pdf_ot, name='generar_pdf_ot'),  # Generar PDF de una orden de trabajo
    
    # ============================================================================
    # APIs PARA ORDEN DE TRABAJO
    # ============================================================================
    # Operaciones AJAX relacionadas con órdenes de trabajo
    path('api/ordenes-trabajo/', views.api_listar_ordenes_trabajo, name='api_listar_ordenes_trabajo'),  # Listar OTs con filtros y paginación
    path('api/ordenes-trabajo/validar-disponibilidad/', views.api_validar_disponibilidad_ot, name='api_validar_disponibilidad_ot'),  # Validar disponibilidad de equipo y personal
    path('api/ordenes-trabajo/guardar/', views.api_guardar_orden_trabajo, name='api_guardar_orden_trabajo'),  # Crear o actualizar OT
    path('api/ordenes-trabajo/<int:ot_id>/observacion/', views.api_agregar_observacion_ot, name='api_agregar_observacion_ot'),  # Agregar observación al historial de OT
    path('api/detalle-ot/<int:ot_id>/', views.api_detalle_ot, name='api_detalle_ot'),  # Obtener detalle completo de una OT
    path('api/ordenes-trabajo/<int:ot_id>/historial/', views.api_historial_ot, name='api_historial_ot'),  # Obtener historial completo de una OT
    
    # APIs auxiliares para formularios de OT
    path('api/equipos-filtrados/', views.api_equipos_filtrados, name='api_equipos_filtrados'),  # Obtener equipos filtrados por empresa/tipo/marca/modelo
    path('api/personal-maquinarias/', views.api_personal_maquinarias, name='api_personal_maquinarias'),  # Obtener personal disponible para asignar
    path('api/marcas-por-tipo/', views.api_marcas_por_tipo, name='api_marcas_por_tipo'),  # Obtener marcas filtradas por tipo (filtro en cascada)
    path('api/modelos-por-tipo-marca/', views.api_modelos_por_tipo_marca, name='api_modelos_por_tipo_marca'),  # Obtener modelos filtrados por tipo y marca (filtro en cascada)
    path('api/pautas/<int:pauta_id>/detalle-ot/', views.api_detalle_pauta_ot, name='api_detalle_pauta_ot'),  # Obtener detalle de pauta para mostrar en OT
    path('api/cargos-por-depto/', views.api_cargos_por_depto, name='api_cargos_por_depto'),  # Obtener cargos filtrados por departamento
    path('api/departamentos/', views.api_departamentos, name='api_departamentos'),  # Obtener todos los departamentos
    
    # ============================================================================
    # APIs PARA HISTORIAL DE EQUIPOS
    # ============================================================================
    # Operaciones relacionadas con el historial de cambios de equipos
    path('api/equipos/<int:equipo_id>/historial/', views.api_historial_equipo, name='api_historial_equipo'),  # Obtener historial completo de un equipo
    
    # ============================================================================
    # DESCARGAS Y EXPORTACIONES
    # ============================================================================
    # Funcionalidades para descargar información en diferentes formatos
    path('equipos/descargar-documentacion-zip/', views.descargar_documentacion_zip_equipos, name='descargar_documentacion_zip_equipos'),  # Descargar documentación de múltiples equipos en ZIP
]

