from django.urls import path
from . import views

app_name = 'calendario'

urlpatterns = [
    path('', views.calendario_mensual, name='calendario_mensual'),
    path('limpiar-cache/', views.limpiar_cache_calendario, name='limpiar_cache'),
    path('api/calendario/', views.api_calendario_mensual, name='api_calendario_mensual'),
    path('api/crear-asignacion/', views.crear_asignacion, name='crear_asignacion'),
    path('api/crear-asignacion-masiva/', views.crear_asignacion_masiva, name='crear_asignacion_masiva'),
    path('api/actualizar-asignacion/', views.actualizar_asignacion, name='actualizar_asignacion'),
    path('api/eliminar-asignacion/', views.eliminar_asignacion, name='eliminar_asignacion'),
    path('api/personal/<int:personal_id>/info/', views.obtener_info_personal, name='obtener_info_personal'),
    
    # Gestión de faenas
    path('faenas/', views.gestionar_faenas, name='gestionar_faenas'),
    path('faenas/<int:faena_id>/asignar/', views.asignar_personal_faena, name='asignar_personal_faena'),
    path('api/crear-faena/', views.crear_faena, name='crear_faena'),
    path('api/actualizar-faena/', views.actualizar_faena, name='actualizar_faena'),
    path('api/eliminar-faena/', views.eliminar_faena, name='eliminar_faena'),
]
