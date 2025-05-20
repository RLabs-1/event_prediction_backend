from rest_framework import serializers
from core.models import UserFcmToken

class RegisterFcmTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFcmToken
        fields = ['fcm_token', 'session_id']
