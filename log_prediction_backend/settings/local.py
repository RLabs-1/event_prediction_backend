"""
Your local development settings
"""
from .base import *

DEBUG = True
ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'event_prediction_db',
        'USER': 'postgres',
        'PASSWORD': '147258magd',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'Zbedat.majd51@gmail.com'
EMAIL_HOST_PASSWORD = 'your_actual_password'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

DOMAIN_URL = 'http://localhost:8000' 