from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from drf_spectacular.utils import extend_schema

from user_management.serializers.fcm_serializers import RegisterFcmTokenSerializer
from user_management.services.fcm_services import register_fcm_token


class RegisterFcmTokenView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=RegisterFcmTokenSerializer,
        responses={201: RegisterFcmTokenSerializer},
    )
    def post(self, request):
        serializer = RegisterFcmTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fcm_token = serializer.validated_data['fcm_token']
        session_id = serializer.validated_data['session_id']

        token_obj = register_fcm_token(
            user=request.user,
            fcm_token=fcm_token,
            session_id=session_id
        )

        return Response(RegisterFcmTokenSerializer(token_obj).data, status=status.HTTP_201_CREATED)

