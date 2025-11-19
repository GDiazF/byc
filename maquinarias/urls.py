from django.urls import path
from . import views

app_name = 'maquinarias'

urlpatterns = [
    # Vistas principales
    path('equipos/', views.lista_equipos, name='lista_equipos'),
    path('equipos/desactivados/', views.equipos_desactivados, name='equipos_desactivados'),
    path('equipos/crear/', views.crear_equipo, name='crear_equipo'),
    path('equipos/<int:equipo_id>/editar/', views.editar_equipo, name='editar_equipo'),
    path('equipos/<int:equipo_id>/documentacion/', views.documentacion_equipo, name='documentacion_equipo'),
    
    # APIs para documentación de maquinarias
    path('api/tipos-documentos/', views.api_tipos_documentos_maquinaria, name='api_tipos_documentos_maquinaria'),
    path('api/equipos/<int:equipo_id>/documentos/', views.api_documentos_equipo, name='api_documentos_equipo'),
    path('api/equipos/<int:equipo_id>/documentos/subir/', views.api_subir_documento_maquinaria, name='api_subir_documento_maquinaria'),
    path('api/documentos/<int:documento_id>/eliminar/', views.api_eliminar_documento_maquinaria, name='api_eliminar_documento_maquinaria'),
    path('api/equipos/<int:equipo_id>/documentos/historial/', views.api_historial_documentos_equipo, name='api_historial_documentos_equipo'),
    
    # APIs para CRUD de equipos
    path('api/equipos/', views.api_listar_equipos, name='api_listar_equipos'),
    path('api/equipos/guardar/', views.api_guardar_equipo, name='api_guardar_equipo'),
    path('api/equipos/<int:equipo_id>/eliminar/', views.api_eliminar_equipo, name='api_eliminar_equipo'),
    path('api/equipos/<int:equipo_id>/toggle-activo/', views.api_toggle_activo_equipo, name='api_toggle_activo_equipo'),
    
    # APIs para obtener datos de selects
    path('api/tipos-equipo/', views.api_tipos_equipo, name='api_tipos_equipo'),
    path('api/marcas-equipo/', views.api_marcas_equipo, name='api_marcas_equipo'),
    path('api/modelos-equipo/', views.api_modelos_equipo, name='api_modelos_equipo'),
    
    # Vistas para Secciones
    path('secciones/', views.lista_secciones, name='lista_secciones'),
    
    # APIs para CRUD de Secciones
    path('api/secciones/', views.api_listar_secciones, name='api_listar_secciones'),
    path('api/secciones/guardar/', views.api_guardar_seccion, name='api_guardar_seccion'),
    path('api/secciones/<int:seccion_id>/eliminar/', views.api_eliminar_seccion, name='api_eliminar_seccion'),
    
    # Vistas para Tipos de Reparación
    path('tipos-reparacion/', views.lista_tipos_reparacion, name='lista_tipos_reparacion'),
    
    # APIs para CRUD de Tipos de Reparación
    path('api/tipos-reparacion/', views.api_listar_tipos_reparacion, name='api_listar_tipos_reparacion'),
    path('api/tipos-reparacion/guardar/', views.api_guardar_tipo_reparacion, name='api_guardar_tipo_reparacion'),
    path('api/tipos-reparacion/<int:tipo_id>/eliminar/', views.api_eliminar_tipo_reparacion, name='api_eliminar_tipo_reparacion'),
    
    # Vistas para Pautas de Mantenimiento
    path('pautas-mantenimiento/', views.lista_pautas_mantenimiento, name='lista_pautas_mantenimiento'),
    path('pautas-mantenimiento/modelo/<int:modelo_id>/', views.ver_pautas_modelo, name='ver_pautas_modelo'),
    path('pautas-mantenimiento/crear/', views.crear_pauta_mantenimiento, name='crear_pauta_mantenimiento'),
    path('pautas-mantenimiento/<int:pauta_id>/editar/', views.editar_pauta_mantenimiento, name='editar_pauta_mantenimiento'),
    
    # APIs para CRUD de Pautas de Mantenimiento
    path('api/pautas-mantenimiento/', views.api_listar_pautas_mantenimiento, name='api_listar_pautas_mantenimiento'),
    path('api/pautas-mantenimiento/modelo/<int:modelo_id>/', views.api_pautas_por_modelo, name='api_pautas_por_modelo'),
    path('api/pautas-mantenimiento/guardar/', views.api_guardar_pauta_mantenimiento, name='api_guardar_pauta_mantenimiento'),
    path('api/pautas-mantenimiento/<int:pauta_id>/', views.api_detalle_pauta, name='api_detalle_pauta'),
    path('api/pautas-mantenimiento/<int:pauta_id>/toggle-activo/', views.api_toggle_activo_pauta, name='api_toggle_activo_pauta'),
    path('api/pautas-mantenimiento/<int:pauta_id>/eliminar/', views.api_eliminar_pauta, name='api_eliminar_pauta'),
    
    # Vista de calendario de maquinarias
    path('calendario-maquinarias/', views.calendario_maquinarias, name='calendario_maquinarias'),
    
    # Vistas para Orden de Trabajo
    path('ordenes-trabajo/', views.lista_ordenes_trabajo, name='lista_ordenes_trabajo'),
    path('ordenes-trabajo/crear/', views.crear_orden_trabajo, name='crear_orden_trabajo'),
    path('ordenes-trabajo/<int:ot_id>/editar/', views.editar_orden_trabajo, name='editar_orden_trabajo'),
    path('ordenes-trabajo/<int:ot_id>/pdf/', views.generar_pdf_ot, name='generar_pdf_ot'),
    
    # APIs para Orden de Trabajo
    path('api/ordenes-trabajo/', views.api_listar_ordenes_trabajo, name='api_listar_ordenes_trabajo'),
    path('api/ordenes-trabajo/guardar/', views.api_guardar_orden_trabajo, name='api_guardar_orden_trabajo'),
    path('api/ordenes-trabajo/<int:ot_id>/observacion/', views.api_agregar_observacion_ot, name='api_agregar_observacion_ot'),
    path('api/equipos-filtrados/', views.api_equipos_filtrados, name='api_equipos_filtrados'),
    path('api/personal-maquinarias/', views.api_personal_maquinarias, name='api_personal_maquinarias'),
    path('api/marcas-por-tipo/', views.api_marcas_por_tipo, name='api_marcas_por_tipo'),
    path('api/modelos-por-tipo-marca/', views.api_modelos_por_tipo_marca, name='api_modelos_por_tipo_marca'),
    path('api/pautas/<int:pauta_id>/detalle-ot/', views.api_detalle_pauta_ot, name='api_detalle_pauta_ot'),
    path('api/detalle-ot/<int:ot_id>/', views.api_detalle_ot, name='api_detalle_ot'),
    path('api/ordenes-trabajo/<int:ot_id>/historial/', views.api_historial_ot, name='api_historial_ot'),
    path('api/cargos-por-depto/', views.api_cargos_por_depto, name='api_cargos_por_depto'),
    path('api/departamentos/', views.api_departamentos, name='api_departamentos'),
    
    # APIs para historial de equipos
    path('api/equipos/<int:equipo_id>/historial/', views.api_historial_equipo, name='api_historial_equipo'),
]

