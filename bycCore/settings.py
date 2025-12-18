# ============================================================================
# CONFIGURACION DE SETTINGS PARA BYCCORE
# ============================================================================
# Este archivo contiene todas las configuraciones del proyecto Django bycCore.
# Generado por 'django-admin startproject' usando Django 5.2.
# 
# Para mas informacion sobre este archivo, ver:
# https://docs.djangoproject.com/en/5.2/topics/settings/
# 
# Para la lista completa de settings y sus valores, ver:
# https://docs.djangoproject.com/en/5.2/ref/settings/
# ============================================================================

from pathlib import Path
from dotenv import load_dotenv
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')


# SECURITY WARNING: don't run with debug turned on in production!
# Para desarrollo local: DEBUG = True
# Para producción AWS: DEBUG = False
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Para desarrollo local, incluir localhost y 127.0.0.1
# Para producción, solo incluir el dominio y IP del servidor

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


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
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bycCore.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# ============================================================================
# PRODUCCIÓN: PostgreSQL en AWS RDS (Configuración Dinámica)
# ============================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv('DB_NAME'),
        "USER": os.getenv('DB_USER'),
        "PASSWORD": os.getenv('DB_PASSWORD'),
        "HOST": os.getenv('DB_HOST'),
        "PORT": os.getenv('DB_PORT', '5432'),
        "OPTIONS": {
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",  # 30 segundos timeout
        },
        # ⚡ OPTIMIZACIÓN: Conexiones persistentes (reutiliza conexiones)
        "CONN_MAX_AGE": 600,  # Mantener conexiones por 10 minutos
        "CONN_HEALTH_CHECKS": True,  # Verificar salud de conexiones
    }
}

# Base de datos SQLite para desarrollo local (DESCOMENTAR para desarrollo)
# DATABASES = {
#      "default": {
#          "ENGINE": "django.db.backends.sqlite3",
#          "NAME": BASE_DIR / "db.sqlite3",
#      }
#  }

# ============================================================================
# CACHE - OPTIMIZADO PARA PRODUCCIÓN CON GUNICORN
# ============================================================================
# DatabaseCache es mejor que LocMemCache cuando tienes múltiples workers de Gunicorn
# porque el caché se comparte entre todos los workers
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',  # Tabla en la BD
        'OPTIONS': {
            'MAX_ENTRIES': 5000,  # Más entradas para producción
            'CULL_FREQUENCY': 4,  # Eliminar 25% cuando está lleno
        }
    }
}

# NOTA: Debes crear la tabla de caché ejecutando:
# python manage.py createcachetable

# Para desarrollo local con un solo proceso, usar LocMemCache:
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'byc-cache',
#         'OPTIONS': {
#             'MAX_ENTRIES': 1000,
#         }
#     }
# }

# ============================================================================
# SESIONES - OPTIMIZADO PARA PRODUCCIÓN
# ============================================================================
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'  # Caché + BD
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 43200  # 12 horas
SESSION_COOKIE_SECURE = False  # Cambiar a True si tienes HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = False  # Solo guardar si se modifica
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# ============================================================================
# PASSWORD HASHERS - PRODUCCIÓN
# ============================================================================
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # Principal
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',  # Fallback
    'django.contrib.auth.hashers.MD5PasswordHasher',  # Para contraseñas antiguas
]

# Para DESARROLLO LOCAL (más rápido), comentar lo de arriba y descomentar:
# PASSWORD_HASHERS = [
#     'django.contrib.auth.hashers.MD5PasswordHasher',  # Rápido para desarrollo
#     'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # Fallback
# ]

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/home/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ⚡ PRODUCCIÓN: Archivos estáticos recolectados aquí
STATIC_ROOT = '/home/ec2-user/proyecto/byc/staticfiles/'

# Para desarrollo local (descomentar):
# STATIC_ROOT = BASE_DIR / 'staticfiles'

# Directorios adicionales donde Django buscara archivos estaticos
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# ============================================================================
# CONFIGURACION DE ARCHIVOS MEDIA - PRODUCCIÓN CON S3
# ============================================================================
# Para producción, usar S3
# Para desarrollo local, descomentar la configuración de abajo y comentar S3

# Desarrollo local (descomentar para usar):
# MEDIA_ROOT = os.path.join(BASE_DIR, 'Documentacion_Personal')
# MEDIA_URL = '/media/'
# DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# ============================================================================
# CONFIGURACION AWS S3 - PRODUCCION EN NUBE (BUCKET PÚBLICO)
# ============================================================================
# IMPORTANTE: Para desarrollo local, comentar toda esta sección S3
# y usar la configuración de archivos locales de arriba
# IMPORTANTE: Las credenciales deben configurarse como variables de entorno
# para mayor seguridad. Nunca hardcodear credenciales en este archivo.
# 
# NOTA: El bucket S3 está configurado como PÚBLICO, por lo que los archivos
# serán accesibles sin necesidad de URLs firmadas.
# 
# CONFIGURACIÓN DEL BUCKET EN AWS:
# 1. Object Ownership debe estar en "Bucket owner enforced" (no permite ACLs)
# 2. Para hacer el bucket público, usar una política de bucket como esta:
#    {
#        "Version": "2012-10-17",
#        "Statement": [
#            {
#                "Sid": "PublicReadGetObject",
#                "Effect": "Allow",
#                "Principal": "*",
#                "Action": "s3:GetObject",
#                "Resource": "arn:aws:s3:::NOMBRE_BUCKET/*"
#            }
#        ]
#    }
# 3. Desactivar "Block public access" si es necesario
# 
# Para configurar variables de entorno en el servidor:
# export AWS_ACCESS_KEY_ID="tu_access_key"
# export AWS_SECRET_ACCESS_KEY="tu_secret_key"
# export AWS_STORAGE_BUCKET_NAME="byc-core-media-files-2025-12-13"
# export AWS_S3_REGION_NAME="us-east-1"

# Credenciales de AWS (obtener desde variables de entorno)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN', '')  # Para AWS Academy
AWS_STORAGE_BUCKET_NAME = 'byc-core-media-files-2025-12-13'  # Nombre correcto del bucket
AWS_S3_REGION_NAME = 'us-east-1'

# Configuración del dominio S3
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# Configuración de seguridad y permisos (BUCKET PÚBLICO)
# NOTA: El bucket no permite ACLs (Object Ownership = Bucket owner enforced)
# La publicidad se controla mediante políticas de bucket, no mediante ACLs
AWS_S3_SIGNATURE_VERSION = 's3v4'  # Protocolo de firma actual
AWS_DEFAULT_ACL = None  # No usar ACLs (el bucket no las permite)
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # Cache de 24 horas para archivos
}

# Configuración de URLs (NO se usan URLs firmadas porque el bucket es público)
AWS_QUERYSTRING_AUTH = False  # No generar URLs firmadas (archivos públicos)
AWS_QUERYSTRING_EXPIRE = 3600  # No se usa, pero se mantiene por compatibilidad

# Configuración de sobrescritura de archivos
# NOTA: El storage personalizado MediaS3Storage maneja la sobrescritura
AWS_S3_FILE_OVERWRITE = False  # No sobrescribir automáticamente (el storage personalizado lo maneja)

# Media files configuration for S3 (BUCKET PÚBLICO)
# Usar storage personalizado que permite sobrescribir archivos cuando sea necesario
# Los archivos serán públicos y accesibles directamente sin URLs firmadas
# ⚡ PRODUCCIÓN: Usando S3 para archivos media
DEFAULT_FILE_STORAGE = 'rrhh_personal.storage.MediaS3Storage'
MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/'

# Validación de credenciales AWS (solo en producción, no en desarrollo)
if not DEBUG:
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        import warnings
        warnings.warn(
            'AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY no están configuradas. '
            'Los archivos no se podrán subir a S3. Configura las variables de entorno.',
            UserWarning
        )

# Static files configuration (mantener en el servidor local)
# Los archivos estáticos (CSS, JS) se sirven desde el servidor, no desde S3
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ============================================================================
# CONFIGURACION DE APSCHEDULER (Tareas periodicas)
# ============================================================================
# Configuracion para django-apscheduler
# El scheduler se ejecuta en background y gestiona tareas periodicas
SCHEDULER_AUTOSTART = True  # Iniciar automaticamente cuando Django arranca
SCHEDULER_API_ENABLED = True  # Habilitar API REST para gestionar trabajos (opcional)

CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(',')
