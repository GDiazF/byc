# ============================================================================
# CONFIGURACION ASGI PARA BYCCORE
# ============================================================================
# ASGI (Asynchronous Server Gateway Interface) configuracion para el proyecto bycCore.
# Expone la aplicacion ASGI como una variable a nivel de modulo llamada 'application'.
# 
# Para mas informacion sobre este archivo, ver:
# https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
# ============================================================================

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bycCore.settings')

application = get_asgi_application()
