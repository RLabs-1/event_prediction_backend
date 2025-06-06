# tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from loguru import logger
from core.models import UserFcmToken  

@shared_task
def clean_expired_fcm_tokens():
    """
    Remove FCM tokens that haven't been used in the last 90 days
    """
    try:
        # Calculate the cutoff date (90 days ago)
        cutoff_date = timezone.now() - timedelta(days=90)
        
        # Find expired tokens
        expired_tokens = UserFcmToken.objects.filter(
            last_used__lt=cutoff_date # lt = less than
        )
        
        # Count before deletion for logging
        expired_count = expired_tokens.count()
        
        if expired_count > 0:
            # Delete expired tokens
            expired_tokens.delete()
            logger.info(f"Successfully deleted {expired_count} expired FCM tokens")
        else:
            logger.info("No expired FCM tokens found to delete")
            
        return f"Cleaned {expired_count} expired FCM tokens"
        
    except Exception as e:
        logger.error(f"Failed to clean expired FCM tokens: {str(e)}")
        raise Exception(f"Failed to clean expired FCM tokens: {str(e)}")