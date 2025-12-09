# ============================================================================
# CONFIGURACION DE URLS DEL PROYECTO BYCCORE
# ============================================================================
# Este archivo define las rutas URL principales del proyecto.
# Incluye las rutas para todas las aplicaciones instaladas.
# ============================================================================
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

# Configuracion de rutas URL principales
urlpatterns = [
    # Panel de administracion de Django
    path('admin/', admin.site.urls),
    
    # Redireccion raiz a login
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),
    
    # Rutas de las aplicaciones
    path('accounts/', include('main_login.urls')),  # Sistema de autenticacion
    path('home/', include('main_home.urls')),  # Pagina principal
    path('users/', include('rrhh_personal.urls')),  # Gestion de personal
    path('gen_settings/', include('gen_settings.urls')),  # Configuraciones generales
    path('calendario/', include('ope_calendario.urls')),  # Calendario y planificacion
    path('maquinarias/', include('maquinarias.urls')),  # Gestion de equipos y maquinarias
    path('reportes/', include('reportes_auditoria.urls')),  # Reportes y auditoria
    path('dashboards/', include('dashboards.urls')),  # Dashboards y metricas
    path('notificaciones/', include('notificaciones.urls')),  # Sistema de notificaciones
    path('vencimientos/', include('vencimientos_documentos.urls')),  # Vencimientos de documentos
]

# En modo DEBUG, servir archivos media desde el sistema de archivos
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)