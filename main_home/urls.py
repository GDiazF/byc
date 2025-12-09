# ============================================================================
# URLS PARA MAIN_HOME
# ============================================================================
# Define las rutas URL para la aplicación main_home:
# - /: Página principal (home)
# - /perfil/: Perfil del usuario
# - /cambiar-contraseña/: Cambiar contraseña del usuario
# ============================================================================

from django.urls import path
from .views import HomeView, perfil_view, cambiar_contraseña_view

app_name = 'home'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('perfil/', perfil_view, name='perfil'),
    path('cambiar-contraseña/', cambiar_contraseña_view, name='cambiar_contraseña'),
]

