from firebase_admin import messaging
from django.utils import timezone
from typing import List
from core.models import UserFcmToken
from message_queue.notification_structure import Notification
import logging

logger = logging.getLogger(__name__)

class FcmService:
    @staticmethod
    def send_notification_to_users(user_ids: List[str], notification: Notification):
        """
        Sends an FCM notification to all FCM tokens of given users and updates 'last_used' timestamp.
        """

        tokens = list(UserFcmToken.objects.filter(user_id__in=user_ids))

        if not tokens:
            logger.info("No FCM tokens found for users: %s", user_ids)
            return

        fcm_tokens = [token.fcm_token for token in tokens]
        if not fcm_tokens:
            return

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=notification.title,
                body=notification.body.get("Message", "")
            ),
            data={
                "severity": notification.severity.value,
                **{k: str(v) for k, v in notification.body.items()}
            },
            tokens=fcm_tokens,
        )

        response_list = messaging.send_each_for_multicast(message)

        success_indexes = [i for i, r in enumerate(response_list) if r.success]
        success_count = len(success_indexes)

        logger.info("FCM: Sent %d/%d messages successfully", success_count, len(fcm_tokens))

        # Update last_used only for tokens that succeeded
        now = timezone.now()
        for i in success_indexes:
            token = tokens[i]
            token.last_used = now
            token.save(update_fields=["last_used"])