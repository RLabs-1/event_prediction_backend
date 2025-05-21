from .base import *
import dj_database_url
from loguru import logger
import sys


DEBUG = False
ALLOWED_HOSTS = ['temp-event-analyzer-fe6caee7f8ac.herokuapp.com']

# Database configuration for Heroku
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # Fallback for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# Additional database settings for performance
DATABASES['default']['CONN_MAX_AGE'] = 600  # Keep connections alive for 10 minutes

# Configure Django middleware to serve static files through Whitenoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Configure static file storage
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Static files settings
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Security settings for Heroku
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Production Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')


# Firebase configuration

#####  This needs to be changed to the actual firebase credentials
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, 'path/to/secure/firebase-credentials.json')

# Production JWT Settings - More strict
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),  # Shorter for production
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
}

# Production Logging - More strict, but with console only for Heroku
#Logging configuration

# Logging configuration
LOG_DIR = os.path.join(BASE_DIR, 'logs') 
os.makedirs(LOG_DIR, exist_ok=True)

# Remove default log handlers to avoid duplicates
logger.remove()

# Log format with more context
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"

# Configure Loguru Handlers
logger.configure(
    handlers=[
        # Debug Log (Logs all messages)
        {
            "sink": os.path.join(LOG_DIR, "debug.log"),
            "level": "DEBUG",
            "rotation": "10 MB",
            "retention": "7 days",
            "format": LOG_FORMAT,
            "enqueue": True,
            "backtrace": True,
            "diagnose": True,
        },
        # Info Log
        {
            "sink": os.path.join(LOG_DIR, "info.log"),
            "level": "INFO",
            "rotation": "10 MB",
            "retention": "7 days",
            "format": LOG_FORMAT,
            "enqueue": True,
        },
        # Warning Log
        {
            "sink": os.path.join(LOG_DIR, "warning.log"),
            "level": "WARNING",
            "rotation": "10 MB",
            "retention": "7 days",
            "format": LOG_FORMAT,
            "enqueue": True,
            "backtrace": True,
        },
        # Error Log
        {
            "sink": os.path.join(LOG_DIR, "error.log"),
            "level": "ERROR",
            "rotation": "10 MB",
            "retention": "7 days",
            "format": LOG_FORMAT,
            "enqueue": True,
            "backtrace": True,
            "diagnose": True,
        },
        # Critical Log
        {
            "sink": os.path.join(LOG_DIR, "critical.log"),
            "level": "CRITICAL",
            "rotation": "10 MB",
            "retention": "7 days",
            "format": LOG_FORMAT,
            "enqueue": True,
            "backtrace": True,
            "diagnose": True,
        },
        # Console Output (for development)
        {
            "sink": sys.stderr,
            "level": "DEBUG" if DEBUG else "INFO",
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            "colorize": True,
            "enqueue": True,
        },
    ]
)
