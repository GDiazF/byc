from django.urls import path
from . import views

app_name = 'maquinarias'

urlpatterns = [
    # Vistas principales
    path('equipos/', views.lista_equipos, name='lista_equipos'),
    path('equipos/desactivados/', views.equipos_desactivados, name='equipos_desactivados'),
    path('equipos/crear/', views.crear_equipo, name='crear_equipo'),
    path('equipos/<int:equipo_id>/editar/', views.editar_equipo, name='editar_equipo'),
    path('equipos/<int:equipo_id>/ficha-tecnica/', views.ficha_tecnica_equipo, name='ficha_tecnica_equipo'),
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
]

