# ============================================================================
# URLS PARA MAIN_LOGIN
# ============================================================================
# Define las rutas URL para la aplicación main_login:
# - /login/: Página de inicio de sesión
# - /logout/: Cerrar sesión
# ============================================================================

from django.contrib.auth import views as auth_views
from django.urls import path
from .views import CustomLoginView


urlpatterns = [
    path('login/', CustomLoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
