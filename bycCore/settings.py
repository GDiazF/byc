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
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-zxiwr5sw3xn%vu+bh47ucrprmj2c@ws#0%+x22if%gcqj16pbx'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
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
    # 'storages',  # Solo para produccion con S3
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

# Base de datos SQLite para desarrollo local (portable)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Base de datos PostgreSQL local para desarrollo (BACKUP)
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": "bycCoreDB",
#         "USER": "postgres",
#         "PASSWORD": "123456",  # Ajusta segun tu configuracion local
#         "HOST": "localhost",
#         "PORT": "5432",
#     }
# }

# Base de datos PostgreSQL en AWS RDS (para produccion)
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": "prototipo_byc",
#         "USER": "postgres",
#         "PASSWORD": "Administrador_prototipo",
#         "HOST": "db-prototipo-byc.c5wkeuesen30.us-east-1.rds.amazonaws.com",
#         "PORT": "5432",
#     }
# }

# Cache configuration
# Configuracion de cache para optimizar rendimiento del calendario y notificaciones
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'byc-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Maximo 1000 entradas en cache
        }
    }
}

# Para produccion con multiples instancias, se recomienda usar Memcached o Redis:
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#     }
# }


# ============================================================================
# PASSWORD HASHERS - OPTIMIZADO PARA DESARROLLO LOCAL
# ============================================================================
# En desarrollo usamos MD5 que es MUCHO mas rapido (solo para desarrollo!)
# Para produccion, comentar esta seccion y usar el PBKDF2 por defecto
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',  # Rapido para desarrollo
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # Fallback para contrasenas existentes
]

# Para PRODUCCION, usar esto en su lugar (comentar lo de arriba):
# PASSWORD_HASHERS = [
#     'django.contrib.auth.hashers.Argon2PasswordHasher',  # Mas seguro que PBKDF2
#     'django.contrib.auth.hashers.PBKDF2PasswordHasher',
#     'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
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

# Para desarrollo local
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Para produccion en servidor
# STATIC_ROOT = '/home/ubuntu/byc/collectedstatic/'

# Directorios adicionales donde Django buscara archivos estaticos
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# ============================================================================
# CONFIGURACION DE ARCHIVOS MEDIA - DESARROLLO LOCAL
# ============================================================================
# Directorio raiz donde se almacenaran todos los archivos subidos (LOCAL)
MEDIA_ROOT = os.path.join(BASE_DIR, 'Documentacion_Personal')

# URL para acceder a los archivos subidos (LOCAL)
MEDIA_URL = '/media/'

# Storage backend por defecto (LOCAL)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# ============================================================================
# CONFIGURACION AWS S3 - PRODUCCION EN NUBE (COMENTADO PARA DESARROLLO)
# ============================================================================
# AWS S3 Configuration
# AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'byc-documentos-bucket')
# AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
# AWS_DEFAULT_ACL = None
# AWS_S3_OBJECT_PARAMETERS = {
#     'CacheControl': 'max-age=86400',
# }

# Media files configuration for S3
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

# Static files configuration (mantener en el servidor)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# ============================================================================
# CONFIGURACION DE APSCHEDULER (Tareas periodicas)
# ============================================================================
# Configuracion para django-apscheduler
# El scheduler se ejecuta en background y gestiona tareas periodicas
SCHEDULER_AUTOSTART = True  # Iniciar automaticamente cuando Django arranca
SCHEDULER_API_ENABLED = True  # Habilitar API REST para gestionar trabajos (opcional)