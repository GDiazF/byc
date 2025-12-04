"""
URLs para el sistema de notificaciones.
"""

from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    path('', views.ver_notificaciones, name='ver_notificaciones'),
    path('api/', views.api_notificaciones, name='api_notificaciones'),
    path('api/contar/', views.api_contar_notificaciones_no_leidas, name='api_contar_notificaciones_no_leidas'),
    path('api/<int:notificacion_id>/marcar-leida/', views.api_marcar_leida, name='api_marcar_leida'),
    path('api/marcar-todas-leidas/', views.api_marcar_todas_leidas, name='api_marcar_todas_leidas'),
    path('api/<int:notificacion_id>/archivar/', views.api_archivar, name='api_archivar'),
    path('api/<int:notificacion_id>/desarchivar/', views.api_desarchivar, name='api_desarchivar'),
]

