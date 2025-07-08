#message_queue/views/fcm_views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from message_queue.serializers.fcm_serializers import (
    FcmTokenRegistrationSerializer,
    FcmTokenResponseSerializer,
)
from message_queue.services.fcm_services import register_fcm_token
from drf_spectacular.utils import extend_schema

@extend_schema(
    request=FcmTokenRegistrationSerializer,
    responses={
        200: FcmTokenResponseSerializer,
        201: FcmTokenResponseSerializer
    },
    tags=["message_queue"]
)
class RegisterFcmTokenView(APIView):
    def post(self, request):
        serializer = FcmTokenRegistrationSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            fcm_token = serializer.validated_data['fcm_token']
            session_id = serializer.validated_data['session_id']

            token, created = register_fcm_token(request.user, fcm_token, session_id)

            response_serializer = FcmTokenResponseSerializer(token)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

            return Response(response_serializer.data, status=status_code)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

