from django.urls import path
from . import views

app_name = 'calendario'

urlpatterns = [
    path('', views.calendario_mensual, name='calendario_mensual'),
    path('api/calendario/', views.api_calendario_mensual, name='api_calendario_mensual'),
    path('api/crear-asignacion/', views.crear_asignacion, name='crear_asignacion'),
    path('api/actualizar-asignacion/', views.actualizar_asignacion, name='actualizar_asignacion'),
    path('api/eliminar-asignacion/', views.eliminar_asignacion, name='eliminar_asignacion'),
]
