from celery import shared_task
from django.utils import timezone
from core.models import EmailVerification

@shared_task
def delete_expired_verification_codes():
    now = timezone.now()
    expired_codes = EmailVerification.objects.filter(token_time_to_live__lt=now) # Lt = less than
    deleted_count, _ = expired_codes.delete()
    return f"Deleted {deleted_count} expired verification codes."
