# ============================================================================
# URLS DE CALENDARIO DE OPERACIONES
# ============================================================================
# Este módulo define las rutas URL para el sistema de calendario de operaciones.
# Incluye vistas principales, APIs para asignaciones y gestión de faenas.

from django.urls import path
from . import views

app_name = 'calendario'

urlpatterns = [
    # ========================================================================
    # VISTAS PRINCIPALES
    # ========================================================================
    path('', views.calendario_mensual, name='calendario_mensual'),  # Vista principal del calendario mensual
    path('limpiar-cache/', views.limpiar_cache_calendario, name='limpiar_cache'),  # Limpiar caché del calendario
    
    # ========================================================================
    # APIs PARA CALENDARIO Y ASIGNACIONES
    # ========================================================================
    path('api/calendario/', views.api_calendario_mensual, name='api_calendario_mensual'),  # API para obtener datos del calendario mensual
    path('api/crear-asignacion/', views.crear_asignacion, name='crear_asignacion'),  # API para crear asignación de personal a faena
    path('api/crear-asignacion-masiva/', views.crear_asignacion_masiva, name='crear_asignacion_masiva'),  # API para crear múltiples asignaciones
    path('api/actualizar-asignacion/', views.actualizar_asignacion, name='actualizar_asignacion'),  # API para actualizar asignación existente
    path('api/eliminar-asignacion/', views.eliminar_asignacion, name='eliminar_asignacion'),  # API para eliminar asignación
    path('api/crear-asignacion-equipos/', views.crear_asignacion_equipos, name='crear_asignacion_equipos'),  # API para crear asignación de equipos a faena
    path('api/actualizar-asignacion-equipo/', views.actualizar_asignacion_equipo, name='actualizar_asignacion_equipo'),  # API para actualizar asignación de equipo
    path('api/eliminar-asignacion-equipo/', views.eliminar_asignacion_equipo, name='eliminar_asignacion_equipo'),  # API para eliminar asignación de equipo
    path('api/personal/<int:personal_id>/info/', views.obtener_info_personal, name='obtener_info_personal'),  # API para obtener información de personal
    
    # ========================================================================
    # GESTIÓN DE FAENAS
    # ========================================================================
    path('faenas/', views.gestionar_faenas, name='gestionar_faenas'),  # Vista principal de gestión de faenas
    path('faenas/<int:faena_id>/asignar/', views.asignar_personal_faena, name='asignar_personal_faena'),  # Vista para asignar personal a faena
    path('faenas/<int:faena_id>/asignar-equipos/', views.asignar_equipos_faena, name='asignar_equipos_faena'),  # Vista para asignar equipos a faena
    path('faenas/<int:faena_id>/historial/', views.ver_historial_faena, name='ver_historial_faena'),  # Vista para ver historial de faena
    path('api/faenas/<int:faena_id>/historial/', views.api_historial_faena, name='api_historial_faena'),  # API para obtener historial de faena
    path('estados-manuales/<int:estado_id>/delete/', views.eliminar_estado_manual, name='eliminar_estado_manual'),  # Vista para eliminar estado manual
    path('api/asignar-estado-manual/', views.asignar_estado_manual_api, name='asignar_estado_manual_api'),  # API para asignar estado manual
    path('api/listar-faenas/', views.listar_faenas_api, name='listar_faenas_api'),  # API para listar faenas
    path('api/crear-faena/', views.crear_faena, name='crear_faena'),  # API para crear faena
    path('api/actualizar-faena/', views.actualizar_faena, name='actualizar_faena'),  # API para actualizar faena
    path('api/eliminar-faena/', views.eliminar_faena, name='eliminar_faena'),  # API para eliminar faena
    
    # ========================================================================
    # APIs PARA CALENDARIO DE FAENA
    # ========================================================================
    path('api/estados/', views.api_estados, name='api_estados'),  # API para obtener lista de estados disponibles
    path('api/personal-faena/<int:faena_id>/', views.api_personal_faena, name='api_personal_faena'),  # API para obtener personal asignado a una faena
]
