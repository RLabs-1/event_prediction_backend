from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'core'
    
    def ready(self):
        import core.signals  # This makes sure the signals are registered
