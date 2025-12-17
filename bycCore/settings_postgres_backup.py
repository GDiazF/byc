# ============================================================================
# CONFIGURACION DE SETTINGS BACKUP POSTGRESQL PARA BYCCORE
# ============================================================================
# Este archivo contiene configuraciones alternativas usando PostgreSQL.
# Es un archivo de respaldo/backup de configuracion.
# 
# Para mas informacion sobre este archivo, ver:
# https://docs.djangoproject.com/en/5.2/topics/settings/
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
DEBUG = False

ALLOWED_HOSTS = ["webapp.gruasbyc.cl","98.94.227.236"]


# Application definition

INSTALLED_APPS = [
    'ope_calendario',
    'main_login',
    'rrhh_personal',
    'main_home',
    'maquinarias',
    'gen_settings',
    'storages',  # Solo para produccion con S3
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

# Base de datos PostgreSQL local para desarrollo
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "bycCore",
        "USER": "postgres",
        "PASSWORD": "Admin12345###",  # Ajusta segun tu Configuracion local
        "HOST": "byccore-db.cjscic8mi81f.us-east-1.rds.amazonaws.com",
        "PORT": "5432",
    }
}

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
# Configuracion de cache para optimizar rendimiento del calendario
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'byc-cache',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Maximo 1000 entradas en cache
        }
    }
}

# Para produccion, se recomienda usar Memcached o Redis:
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#     }
# }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
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

LANGUAGE_CODE = 'es-cl'

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
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Para produccion en servidor
# STATIC_ROOT = '/home/ubuntu/byc/collectedstatic/'

# Directorios adicionales donde Django buscara archivos estaticos
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# ============================================================================
# Configuracion DE ARCHIVOS MEDIA - DESARROLLO LOCAL
# ============================================================================
# Directorio raiz donde se almacenaran todos los archivos subidos (LOCAL)
MEDIA_ROOT = os.path.join(BASE_DIR, 'Documentacion_Personal')

# URL para acceder a los archivos subidos (LOCAL)
MEDIA_URL = '/media/'

# Storage backend por defecto (LOCAL)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# ============================================================================
# Configuracion AWS S3 - produccion EN NUBE (COMENTADO PARA DESARROLLO)
# ============================================================================

AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'byc-documentos-bucket')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False



CSRF_TRUSTED_ORIGINS = ['https://webapp.gruasbyc.cl', 'https://98.94.227.236']

# Media files configuration for S3
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

# Static files configuration (mantener en el servidor)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
