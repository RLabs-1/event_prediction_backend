# views.py
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.services.services import RegistrationService
from user_management.serializers.serializers import RegistrationSerializer, UserUpdateSerializer
from rest_framework import generics,  permissions

from user_management.models.models import User
from user_management.services.services import UserService
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from core.models import User
from django.shortcuts import render
from user_management.services.services import UserService
from django.contrib.auth import authenticate
from user_management.services.services import JWTService
from drf_spectacular.utils import extend_schema
from django.shortcuts import render

from rest_framework import status
from django.contrib.auth import authenticate

User = get_user_model()



class RegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.validated_data
            user_service = RegistrationService()
            user = user_service.register_user(user_data)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class UserUpdateView(generics.RetrieveUpdateAPIView):
    """View for updating User details"""
    permission_classes = (permissions.IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    lookup_field = 'id'

    http_method_names = ['patch']

    def get_object(self):
        # Ensure the user is retrieved based on the URL parameter
        user_id = self.kwargs.get('user_id')
        return generics.get_object_or_404(User, id=user_id)

class ActivateUserView(APIView):
    def patch(self, request, user_id):
        """
        Activates the user account for given user id.
        """
        service_response = UserService.activate_user(user_id)
        if service_response['success']:
            return Response(service_response, status=status.HTTP_200_OK)
        return Response(service_response, status=status.HTTP_400_BAD_REQUEST)
class UserLoginView(APIView):
    """
    Handles user login and returns a JWT token.
    """
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)


        # Authenticate user
        user = authenticate(email=email, password=password)
        if user is not None:
            tokens = JWTService.create_token(user) # Generate JWT token using JWTService
            return Response({
                "refresh": tokens["refresh"],
                "access": tokens["access"],
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)


class ForgotPasswordView(APIView):
    def post(self, request):
        """
        Initiates the password reset process for a user
        """
        email = request.data.get('email')
        
        if not email:
            return Response({
                'success': False,
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service_response = UserService.initiate_password_reset(email)
        
        if service_response['success']:
            return Response(service_response, status=status.HTTP_200_OK)
        return Response(service_response, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Reset Forgotten Password",
    description="This endpoint allows users to reset their forgotten password by providing the email, verification code, and new password.",
    request={
        'type': 'object',
        'properties': {
            'email': {'type': 'string', 'format': 'email'},
            'new_password': {'type': 'string'},
            'confirm_password': {'type': 'string'},
            'verification_code': {'type': 'string'}
        }
    },
    responses={
        200: {'description': 'Password reset successfully'},
        400: {'description': 'Bad Request'},
        403: {'description': 'Forbidden'},
        404: {'description': 'User not found'},
        410: {'description': 'Verification code expired'},
    }
)
class ResetForgotPasswordView(APIView):
    def post(self, request):
        try:
            data = request.data
            email = data.get('email')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')
            verification_code = data.get('verification_code')

            if new_password != confirm_password:
                return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve the user based on email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # Check if the verification code is -1 (Forbidden)
            if user.verification_code == '-1':
                return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

            # Check if the token has expired
            if user.is_token_expired():
                return Response({"error": "Verification code expired"}, status=status.HTTP_410_GONE)

            # Check if the verification code matches
            if user.verification_code != verification_code:
                return Response({"error": "Invalid verification code"}, status=status.HTTP_400_BAD_REQUEST)

            # Reset the password and update the necessary fields
            user.set_password(new_password)
            user.is_password_reset_pending = False
            user.verification_code = '-1'
            user.save()

            return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)

        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



