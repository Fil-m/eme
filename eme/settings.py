from pathlib import Path
import os

# Monkeypatch for Python 3.12+ compatibility with old ssl wrappers (like django-sslserver)
import ssl
if not hasattr(ssl, 'wrap_socket'):
    def wrap_socket(sock, **kwargs):
        # Create a default context for server side if not specified
        purpose = ssl.Purpose.CLIENT_AUTH if kwargs.get('server_side', False) else ssl.Purpose.SERVER_AUTH
        context = ssl.create_default_context(purpose)
        
        # Load cert if provided
        certfile = kwargs.pop('certfile', None)
        keyfile = kwargs.pop('keyfile', None)
        if certfile:
            context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        
        # Pull parameters that wrap_socket used to take
        server_side = kwargs.pop('server_side', False)
        do_handshake_on_connect = kwargs.pop('do_handshake_on_connect', True)
        suppress_ragged_eofs = kwargs.pop('suppress_ragged_eofs', True)
        
        return context.wrap_socket(
            sock, 
            server_side=server_side, 
            do_handshake_on_connect=do_handshake_on_connect,
            suppress_ragged_eofs=suppress_ragged_eofs
        )
    ssl.wrap_socket = wrap_socket

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-eme-os-shell-core-key'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'profiles',
    'system_settings',
    'eme_nav',
    'eme_media',
    'network',
    'clone_master',
    'projects',
    'eme_ai',
    'eme_kb',
    'eme_chat',
    'park_adventures',
    'eme_mafia',
    'eme_utils',
    'sslserver',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'profiles.middleware.UpdateLastSeenMiddleware',
]

ROOT_URLCONF = 'eme.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'staticfiles': 'django.templatetags.static',
            },
        },
    },
]

WSGI_APPLICATION = 'eme.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'kb': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'kb.sqlite3',
    },
    'media': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'media.sqlite3',
    },
    'ai': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'ai.sqlite3',
    },
    'kanban': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'kanban.sqlite3',
    },
    'game': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'game.sqlite3',
    },
    'social': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'social.sqlite3',
    },
    'mafia': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'mafia.sqlite3',
    },
    'utils': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'utils.sqlite3',
    }
}

DATABASE_ROUTERS = ['eme.db_router.ModuleRouter']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uk-ua'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User
AUTH_USER_MODEL = 'profiles.EMEUser'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '100/minute',
    },
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

CORS_ALLOW_ALL_ORIGINS = True

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB

# Security Settings for HTTPS
if 'sslserver' in INSTALLED_APPS:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # SECURE_SSL_REDIRECT = False # Keep False for local dev to avoid infinite loops if not properly proxied
