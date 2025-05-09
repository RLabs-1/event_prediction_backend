# File: settings/base.py
# This contains all the common settings shared between local and production
from pathlib import Path
import os
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'user_management.apps.UserManagementConfig',
    'rest_framework',
    'drf_spectacular',
    'core',
    'corsheaders',
    'django_celery_beat',

    'django_prometheus',

    'storages',
    

]

AUTH_USER_MODEL = 'core.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True


# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # URL for Redis
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'



ROOT_URLCONF = 'log_prediction_backend.urls'

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

WSGI_APPLICATION = 'log_prediction_backend.wsgi.application'
STATIC_ROOT = 'staticfiles'

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Rest Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'user_management.utils.exception_handler.custom_exception_handler',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Log Prediction API',
    'DESCRIPTION': 'API documentation for Log Prediction',
    'VERSION': '1.0.0',
}

AUTHENTICATION_BACKENDS = [
    'user_management.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# # S3 Storage settings
# AWS_ACCESS_KEY_ID = "your-access-key"  # Replace with the actual key
# AWS_SECRET_ACCESS_KEY = "your-secret-key"  # Replace with the actual secret
# AWS_STORAGE_BUCKET_NAME = "your-bucket-name"  # Replace with the bucket name
# AWS_S3_REGION_NAME = "your-region"  # Replace with the AWS region (e.g., 'us-west-2')
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
#
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'


# # SCP Storage settings
# SCP_HOST = 'example.com'  # Replace with SCP server's hostname or IP address
# SCP_PORT = 22  # Default SCP port
# SCP_USER = 'your_username'  # Replace with SCP username
# SCP_PASSWORD = 'your_password'  # Replace with SCP password (or use SSH key authentication)
# SCP_REMOTE_PATH = '/path/to/remote/directory'  # The directory we want to store the files