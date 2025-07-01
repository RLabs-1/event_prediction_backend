from firebase_admin import messaging
from django.utils import timezone
from typing import List
from core.models import UserFcmToken
from message_queue.notification_structure import Notification
import logging
logger = logging.getLogger(__name__)
import requests
from django.utils.timezone import now

class FCMService:
    """
    Service for sending push notifications via Firebase Cloud Messaging (FCM).
    """

    FCM_ENDPOINT = 'https://fcm.googleapis.com/fcm/send'

    def __init__(self, server_key: str):

        self.server_key = server_key
        self.headers = {
            'Authorization': f'key={self.server_key}',
            'Content-Type': 'application/json'
        }

    def send_to_token(self, token: str, title: str, body: str, data: dict = None) -> dict:

        payload = {
            'to': token,
            'notification': {
                'title': title,
                'body': body
            },
            'data': data or {}
        }

        return self._send(payload)

    def send_to_multiple(self, tokens: list, title: str, body: str, data: dict = None) -> dict:

        payload = {
            'registration_ids': tokens,
            'notification': {
                'title': title,
                'body': body
            },
            'data': data or {}
        }

        return self._send(payload)

    def _send(self, payload: dict) -> dict:

        try:
            response = requests.post(self.FCM_ENDPOINT, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"FCM send failed: {e}")
            return {'error': str(e)}

    def register_token(self, user, token: str, session_id: str = None) -> UserFcmToken:

        obj, created = UserFcmToken.objects.update_or_create(
            user=user,
            fcm_token=token,
            defaults={
                'session_id': session_id or '',
                'updated_at': now(),
            }
        )
        if created:
            print("New token registered.")
        else:
            print("Existing token updated.")
        return obj


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