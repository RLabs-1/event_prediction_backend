# Database configurations
from .base import *
from loguru import logger
import sys
import os

DATABASES = {
    'default': {

        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'event_prediction_db',

        'USER': 'lianmassarwa',
        'PASSWORD': 'lian0192',
        'HOST': 'localhost',
        'PORT': '5433',
    }
}


DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'temp-event-analyzer-fe6caee7f8ac.herokuapp.com']

# Firebase Cloud
FCM_SERVER_KEY = 'dummy_firebase_key'

SECRET_KEY = 'django-insecure-(7v(oyc&1ixz5onr=$3gg8idp)!3^toob!#i7#%2t6*ts=wv'

# Development Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'eventprediction.backend@gmail.com'
EMAIL_HOST_PASSWORD = 'ledz sibu oocn lcwo'
DEFAULT_FROM_EMAIL = 'eventprediction.backend@gmail.com'

# Development JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Longer for development
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
