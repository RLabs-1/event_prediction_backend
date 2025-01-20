from django.contrib.auth import get_user_model, authenticate
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from user_management.services.services import RegistrationService, UserService, JWTService
from user_management.serializers.serializers import RegistrationSerializer, UserUpdateSerializer, UserDeactivateSerializer
from user_management.models.models import User
from drf_spectacular.utils import extend_schema
from django.http import JsonResponse
import json

User = get_user_model()

class RegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.validated_data
            user_service = RegistrationService()
            user_service.register_user(user_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserUpdateView(generics.RetrieveUpdateAPIView):
    """View for updating User details."""
    permission_classes = (permissions.IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    lookup_field = 'id'
    http_method_names = ['patch']

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        return generics.get_object_or_404(User, id=user_id)

class ActivateUserView(APIView):
    """Activates a user account."""
    def patch(self, request, user_id):
        service_response = UserService.activate_user(user_id)
        if service_response['success']:
            return Response(service_response, status=status.HTTP_200_OK)
        return Response(service_response, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    """Handles user login and returns a JWT token."""
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        
        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(email=email, password=password)
        
        if user:
            tokens = JWTService.create_token(user)
            return Response({"refresh": tokens["refresh"], "access": tokens["access"]}, status=status.HTTP_200_OK)
        
        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

class UserDeactivateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, userId):
        """Deactivates a user by their ID."""
        try:
            user = UserService.deactivate_user(userId)
            serializer = UserDeactivateSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

class ForgotPasswordView(APIView):
    def post(self, request):
        """Initiates the password reset process."""
        email = request.data.get('email')
        
        if not email:
            return Response({'success': False, 'message': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        service_response = UserService.initiate_password_reset(email)
        
        return Response(service_response, status=status.HTTP_200_OK if service_response['success'] else status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Reset Forgotten Password",
    description="Allows users to reset their forgotten password by providing email, verification code, and new password.",
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
        data = request.data
        email = data.get('email')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        verification_code = data.get('verification_code')

        if new_password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if user.verification_code == '-1':
                return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
            
            if user.is_token_expired():
                return Response({"error": "Verification code expired"}, status=status.HTTP_410_GONE)
            
            if user.verification_code != verification_code:
                return Response({"error": "Invalid verification code"}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.is_password_reset_pending = False
            user.verification_code = '-1'
            user.save()

            return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyEmailView(APIView):
    """Handles email verification by verifying the provided code."""
    def post(self, request):
        email = request.data.get("email")
        verification_code = request.data.get("verification_code")
        
        if not email or not verification_code:
            return Response({"error": "Email and verification code are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        service_response = RegistrationService.verify_email(email, verification_code)
        
        if "successfully" in service_response["message"]:
            return Response(service_response, status=status.HTTP_200_OK)
        
        return Response(service_response, status=status.HTTP_400_BAD_REQUEST)

def user_register(request):
    user_email = "raneem.dz34@gmail.com"  # We should use the registered email
    email_service = EmailService()
    try:
        email_service.send_email(user_email)
        return JsonResponse({"message": "User registered and email sent successfully!"})
    except Exception as e:
        return JsonResponse({"error": f"Failed to send email: {str(e)}"}, status=500)

def user_view(request):
    """Handles requests to /api/user"""
    user_data = {
        'username': 'example_user',
        'email': 'user@example.com'
    }
    return JsonResponse(user_data)
