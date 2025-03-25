from celery import Celery
from celery.schedules import crontab

# Create Celery app instance
app = Celery('log_prediction_backend')

# Celery Configuration
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Periodic task to delete expired codes every 24 hours 
app.conf.beat_schedule = {
    'delete-expired-codes-every-24-hours': {  # Just a unique identifier/name for this task
        'task': 'user_management.services.tasks.delete_expired_verification_codes', # The path for the task
        'schedule': crontab(minute=0, hour=0),  # This runs daily at midnight
    },
}

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
