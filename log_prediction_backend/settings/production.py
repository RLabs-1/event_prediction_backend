"""
Production settings
"""
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['your-production-domain.com']

# Add your production database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'production_db',
        'USER': 'production_user',
        'PASSWORD': 'production_password',
        'HOST': 'production_host',
        'PORT': '5432',
    }
}

# Production email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'production_email@gmail.com'
EMAIL_HOST_PASSWORD = 'production_app_password'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

DOMAIN_URL = 'https://your-production-domain.com' 