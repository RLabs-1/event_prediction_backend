#message_queue/serializers/fcm_serializers.py


from rest_framework import serializers
from core.models import UserFcmToken


class FcmTokenRegistrationSerializer(serializers.Serializer):
    #Serializer for FCM token registration
    fcm_token = serializers.CharField(max_length=128, required=True)
    session_id = serializers.CharField(max_length=38, required=True)

    def validate_fcm_token(self, value):
        #Validate FCM token format
        if not value or not value.strip():
            raise serializers.ValidationError("FCM token cannot be empty")

        return value.strip()

    def validate_session_id(self, value):
        #Validate session ID format
        if not value or not value.strip():
            raise serializers.ValidationError("Session ID cannot be empty")

        return value.strip()

class FcmTokenResponseSerializer(serializers.ModelSerializer):
    #Serializer for FCM token response
    class Meta:
        model = UserFcmToken
        fields = ['id', 'fcm_token', 'session_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']