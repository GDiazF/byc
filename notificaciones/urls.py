# ============================================================================
# URLS PARA EL SISTEMA DE NOTIFICACIONES
# ============================================================================
# Define las rutas URL para la aplicación notificaciones:
# - /notificaciones/: Página principal de notificaciones
# - /notificaciones/api/: API para obtener notificaciones
# - /notificaciones/api/contar/: API para contar notificaciones no leídas
# - /notificaciones/api/sse/: Server-Sent Events para notificaciones en tiempo real
# - /notificaciones/api/<id>/marcar-leida/: API para marcar notificación como leída
# - /notificaciones/api/marcar-todas-leidas/: API para marcar todas como leídas
# - /notificaciones/api/<id>/archivar/: API para archivar notificación
# - /notificaciones/api/<id>/desarchivar/: API para desarchivar notificación
# ============================================================================

from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    path('', views.ver_notificaciones, name='ver_notificaciones'),
    path('api/', views.api_notificaciones, name='api_notificaciones'),
    path('api/contar/', views.api_contar_notificaciones_no_leidas, name='api_contar_notificaciones_no_leidas'),
    path('api/sse/', views.sse_notificaciones, name='sse_notificaciones'),
    path('api/<int:notificacion_id>/marcar-leida/', views.api_marcar_leida, name='api_marcar_leida'),
    path('api/marcar-todas-leidas/', views.api_marcar_todas_leidas, name='api_marcar_todas_leidas'),
    path('api/<int:notificacion_id>/archivar/', views.api_archivar, name='api_archivar'),
    path('api/<int:notificacion_id>/desarchivar/', views.api_desarchivar, name='api_desarchivar'),
]

