# ============================================================================
# CONFIGURACION WSGI PARA BYCCORE
# ============================================================================
# WSGI (Web Server Gateway Interface) configuracion para el proyecto bycCore.
# Expone la aplicacion WSGI como una variable a nivel de modulo llamada 'application'.
# 
# Para mas informacion sobre este archivo, ver:
# https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
# ============================================================================

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bycCore.settings_aws_optimized')
application = get_wsgi_application()
