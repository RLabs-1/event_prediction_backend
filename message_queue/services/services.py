import requests
import logging
from core.models import UserFcmToken
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