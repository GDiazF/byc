# ============================================================================
# CONFIGURACION OPTIMIZADA PARA PRODUCCION AWS (EC2 + RDS + S3)
# ============================================================================
# Este archivo contiene configuraciones optimizadas para AWS que resuelven
# el problema de lentitud en recargas de página.
# 
# USAR ESTE ARCHIVO EN PRODUCCIÓN AWS
# ============================================================================

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-zxiwr5sw3xn%vu+bh47ucrprmj2c@ws#0%+x22if%gcqj16pbx'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["webapp.gruasbyc.cl", "98.94.227.236"]


# Application definition
INSTALLED_APPS = [
    'storages',  # Necesario para S3 en producción (django-storages)
    'ope_calendario',
    'main_login',
    'rrhh_personal',
    'main_home',
    'maquinarias',
    'gen_settings',
    'gen_permissions',  # App para gestion de roles y permisos
    'reportes_auditoria',
    'dashboards',
    'notificaciones',  # App para sistema de notificaciones
    'vencimientos_documentos',  # App para gestion de vencimientos de documentos
    'django_apscheduler',  # Para tareas periodicas
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'gen_permissions.middleware.PermissionDeniedMiddleware',  # Manejo de errores de permisos
]

ROOT_URLCONF = 'bycCore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bycCore.wsgi.application'


# ============================================================================
# DATABASE - OPTIMIZADO PARA AWS RDS CON CONEXIONES PERSISTENTES
# ============================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "bycCore",
        "USER": "postgres",
        "PASSWORD": "Admin12345###",
        "HOST": "byccore-db.cjscic8mi81f.us-east-1.rds.amazonaws.com",
        "PORT": "5432",
        "OPTIONS": {
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",  # 30 segundos timeout para queries
        },
        # ⚡ CONEXIONES PERSISTENTES: Reutiliza conexiones en lugar de abrir nuevas cada vez
        # Esto elimina la latencia de conectar a RDS en cada request
        "CONN_MAX_AGE": 600,  # Mantener conexiones abiertas por 10 minutos
        # Pool de conexiones para mejor rendimiento
        "CONN_HEALTH_CHECKS": True,  # Verificar que la conexión esté viva antes de usarla
    }
}

# ============================================================================
# CACHE - OPTIMIZADO PARA MÚLTIPLES INSTANCIAS Y SESIONES
# ============================================================================
# Usar caché en base de datos para sesiones (más confiable que LocMem en producción)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
            'CULL_FREQUENCY': 4,  # Eliminar 1/4 de las entradas cuando se alcanza MAX_ENTRIES
        }
    }
}

# Para crear la tabla de caché, ejecutar: python manage.py createcachetable

# ============================================================================
# SESIONES - OPTIMIZADO PARA AWS
# ============================================================================
# Guardar sesiones en caché en lugar de la base de datos principal
# Esto reduce significativamente las queries en cada request
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'  # Usar caché con fallback a BD
SESSION_CACHE_ALIAS = 'default'

# Configuración de cookies de sesión
SESSION_COOKIE_AGE = 43200  # 12 horas (en segundos)
SESSION_COOKIE_SECURE = True  # Solo HTTPS en producción
SESSION_COOKIE_HTTPONLY = True  # No accesible desde JavaScript
SESSION_COOKIE_SAMESITE = 'Lax'  # Protección CSRF

# No guardar sesión en cada request si no cambió (reduce escrituras a BD)
SESSION_SAVE_EVERY_REQUEST = False

# Expirar sesión al cerrar navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# ============================================================================
# PASSWORD HASHERS - PRODUCCIÓN
# ============================================================================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Más seguro
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 13,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ============================================================================
# INTERNATIONALIZATION
# ============================================================================
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True


# ============================================================================
# STATIC FILES
# ============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = '/home/ec2-user/byc/staticfiles/'  # Ajustar según tu configuración

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# ============================================================================
# MEDIA FILES - AWS S3
# ============================================================================
# Configuración de AWS S3 para almacenar archivos media
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')  # Configurar en variables de entorno
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'byccoredocuments'
AWS_S3_REGION_NAME = 'us-east-1'
AWS_DEFAULT_ACL = None
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 1 día de caché para archivos
}

# ⚡ OPTIMIZACIONES S3 CRÍTICAS PARA RENDIMIENTO
AWS_QUERYSTRING_AUTH = False  # No generar URLs firmadas (más rápido)
AWS_S3_FILE_OVERWRITE = False  # No verificar archivos existentes cada vez
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_VERIFY = True  # Verificar certificados SSL

# Storage para archivos media
DEFAULT_FILE_STORAGE = 'rrhh_personal.storage.MediaS3Storage'

# URL pública de S3
MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/'


# ============================================================================
# SEGURIDAD PARA PRODUCCIÓN
# ============================================================================
SECURE_SSL_REDIRECT = False  # Cambiar a True si tienes HTTPS configurado
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# CSRF
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# ============================================================================
# URLS
# ============================================================================
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/home/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================================
# LOGGING PARA DIAGNÓSTICO
# ============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/home/ec2-user/byc/logs/django.log',  # Ajustar ruta
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Cambiar a DEBUG para ver queries SQL
            'propagate': False,
        },
    },
}

