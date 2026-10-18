"""Django settings for the Videoflix project."""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    default='django-insecure-local-development-key',
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', default='False') == 'True'

ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS', default='localhost'
).split(',')
CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS', default='http://localhost:4200'
).split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_rq',
    'auth_app',
    'video_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'


# Database, cache and background queue

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', default='videoflix_db'),
        'USER': os.environ.get('DB_USER', default='videoflix_user'),
        'PASSWORD': os.environ.get(
            'DB_PASSWORD', default='supersecretpassword'
        ),
        'HOST': os.environ.get('DB_HOST', default='db'),
        'PORT': os.environ.get('DB_PORT', default=5432),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get(
            'REDIS_LOCATION', default='redis://redis:6379/1'
        ),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'videoflix',
    }
}

RQ_QUEUES = {
    'default': {
        'HOST': os.environ.get('REDIS_HOST', default='redis'),
        'PORT': os.environ.get('REDIS_PORT', default=6379),
        'DB': os.environ.get('REDIS_DB', default=0),
        'DEFAULT_TIMEOUT': 900,
        'REDIS_CLIENT_KWARGS': {},
    },
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static and media files

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# STATICFILES_STORAGE was removed in Django 5.1, STORAGES replaces it.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'auth_app.api.authentication.CookieJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


# JWT in HttpOnly cookies

# 60 minutes: the frontend never refreshes while a video is playing.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    # last_login invalidates old activation links
    'UPDATE_LAST_LOGIN': True,
}

# Only works over HTTPS, so it stays off locally.
JWT_COOKIE_SECURE = os.getenv('JWT_COOKIE_SECURE', default='False') == 'True'


# CORS

CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS', default='http://127.0.0.1:5500'
).split(',')
CORS_ALLOW_CREDENTIALS = True

FRONTEND_URL = os.getenv('FRONTEND_URL', default='http://127.0.0.1:5500')


# Email, console backend until an SMTP host is set

EMAIL_HOST = os.getenv('EMAIL_HOST', default='')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', default='587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', default='True') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', default='False') == 'True'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)

if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Activation and reset links, 24 hours as the reset mail says
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24
