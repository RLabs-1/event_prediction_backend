# message_queue/services/fcm_services.py

from core.models import UserFcmToken
from django.utils import timezone

def register_fcm_token(user, fcm_token, session_id):
    """
    Registers or updates the FCM token for a user/session.
    Returns:  tuple: (UserFcmToken instance, boolean `created`)
    """
    token, created = UserFcmToken.objects.update_or_create(
        user=user,
        session_id=session_id,
        defaults={
            'fcm_token': fcm_token,
            'last_used': timezone.now(),
        }
    )
    return token, created
