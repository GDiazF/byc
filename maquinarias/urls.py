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
]

