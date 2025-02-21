# settings/__init__.py
import os

environment = os.environ.get('DJANGO_ENVIRONMENT', 'local')  # Defaults to 'local'

if environment == 'production':
    from .production import *
else:
    from .local import *