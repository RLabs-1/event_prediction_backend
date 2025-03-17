# views.py
from django.contrib.auth import get_user_model, authenticate
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from user_management.services.services import RegistrationService, UserService, JWTService, UserDeletedException
from user_management.serializers.serializers import RegistrationSerializer, UserUpdateSerializer, UserDeactivateSerializer
from core.models import User
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from django.http import JsonResponse
from user_management.exceptions.custom_exceptions import (
    UserNotFoundException,
    UserInactiveException,
)
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class UserDeleteView(APIView):
    permissions = [IsAuthenticated]

    @extend_schema(
        tags=['User Management'],
        description='Delete User.',
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of your account to delete'
            ),
        ],
        responses={
            204: {},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied - Can only delete your own account'},
            404: {'description': 'User not found'},
        }
    )

    def delete(self,request, user_id):
        """Delete User"""
        try:
            if request.user.id != user_id:
                return Response(
                    {"error": "You can only delete your own account"},
                    status=status.HTTP_403_FORBIDDEN
                )
            UserService.delete_user(user_id)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except UserDeletedException or UserNotFoundException:
            return Response({"error": "User Not Found"}, status=status.HTTP_404_NOT_FOUND)


User = get_user_model()

class RegistrationView(APIView):
    @extend_schema(
        tags=['User Management'],
        description='Register a new user',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'format': 'email'},
                    'password': {'type': 'string'},
                    'name': {'type': 'string'},
                },
                'required': ['email', 'password', 'name']
            }
        },
        responses={
            201: {
                'description': 'User registered successfully',
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                }
            },
            400: {'description': 'Bad request - validation error'},
        },
        examples=[
            OpenApiExample(
                'Registration Example',
                value={
                    'email': 'user@gmail.com',
                    'password': 'password',
                    'name': 'Name'
                },
                request_only=True
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.validated_data
            user_service = RegistrationService()
            user = user_service.register_user(user_data)

            return Response({'id': user.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['User Management'],
        description='Update user information (except email and staff status). Users can only update their own information.',
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of the user to update (must be your own ID)'
            )
        ],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': 'New name for the user'},
                    'current_password': {'type': 'string', 'description': 'Current password (required for password update)'},
                    'new_password': {'type': 'string', 'description': 'New password'}
                },
            }
        },
        responses={
            204: {},
            400: {'description': 'Bad request - Invalid data or incorrect current password'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'User not found'}
        }
    )
    def patch(self, request, user_id):
        try:
            # Get the user from the token
            requesting_user = request.user
            
            # Check if user is trying to update their own information
            if requesting_user.id != user_id:
                return Response(
                    {"error": "You can only update your own information"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get the user to update (should be the same as requesting user)
            user = User.objects.get(id=user_id)
            
            # Prevent updating email or staff status
            if 'email' in request.data or 'is_staff' in request.data or 'is_active' in request.data:
                return Response(
                    {"error": "Cannot update email, staff status, or active status"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update user data
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class UserLoginView(APIView):
    @extend_schema(
        tags=['User Management'],
        description='Login user and get JWT token',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'format': 'email'},
                    'password': {'type': 'string'},
                },
                'required': ['email', 'password']
            }
        },
        responses={
            200: {
                'description': 'Login successful',
                'type': 'object',
                'properties': {
                    'refresh': {'type': 'string'},
                    'access': {'type': 'string'},
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Invalid credentials'},
            403: {'description': 'Email not verified'},
            404: {'description': 'User not found'}
        }
    )
    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not email or not password:
                return Response({
                    "error": "Email and password are required."
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = authenticate(request, username=email, password=password)
            
            if user:
                # Check if email is verified
                if not user.is_verified:
                    return Response({
                        "error": "Please verify your email before logging in. Check your inbox for the verification code."
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Set user as active when logging in
                user.is_active = True
                user.save()
                
                tokens = JWTService.create_token(user)
                return Response({
                    "refresh": tokens["refresh"],
                    "access": tokens["access"],
                    "message": "Login successful"
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Invalid credentials."
                }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ForgotPasswordView(APIView):
    @extend_schema(
        tags=['User Management'],
        description='Request password reset by providing email',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'format': 'email'},
                },
                'required': ['email']
            }
        },
        responses={
            200: {'description': 'Password reset initiated successfully'},
            400: {'description': 'Email is required or invalid'},
            404: {'description': 'User not found'}
        }
    )
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            service_response = UserService.initiate_password_reset(email)
            return Response(service_response, status=status.HTTP_200_OK)
        except ValueError as ve:
            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)


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
    @extend_schema(
        tags=['User Management'],
        description='Reset forgotten password using verification code',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'format': 'email'},
                    'verification_code': {'type': 'string'},
                    'new_password': {'type': 'string'},
                    'confirm_password': {'type': 'string'}
                },
                'required': ['email', 'verification_code', 'new_password', 'confirm_password']
            }
        },
        responses={
            200: {'description': 'Password reset successfully'},
            400: {'description': 'Invalid data or verification code'},
            404: {'description': 'User not found'},
            410: {'description': 'Verification code expired'}
        }
    )
    def post(self, request):
        try:
            # Get all required fields
            email = request.data.get('email')
            verification_code = request.data.get('verification_code')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')

            # Validate all fields are present
            if not all([email, verification_code, new_password, confirm_password]):
                return Response({
                    'error': 'All fields are required: email, verification_code, new_password, confirm_password'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if passwords match
            if new_password != confirm_password:
                return Response({
                    'error': 'Passwords do not match'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Get user by email
                user = User.objects.get(email=email)

                # Verify the code
                if not user.verification_code or user.verification_code != verification_code:
                    return Response({
                        'error': 'Invalid verification code'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check if code is expired
                if user.is_token_expired():
                    return Response({
                        'error': 'Verification code has expired'
                    }, status=status.HTTP_410_GONE)

                # Reset password
                user.set_password(new_password)
                user.verification_code = None  # Clear the verification code
                user.token_time_to_live = None  # Clear the expiry
                user.is_password_reset_pending = False
                user.save()

                return Response({
                    'message': 'Password reset successfully'
                }, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

          


          
##Bet-30##
def user_view(request):
    #A function that handles requests to /api/user
    #I still don't know what specific data we need, so meanwhile I used these, but I can replace it later with actual database queries

    user_data = {
        'username': 'example_user',
        'email': 'user@example.com'
    }
    return JsonResponse(user_data)          
##Bet-30##  


class UserLogoutView(APIView):
    """
    Handles user logout and deactivates the account.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['User Management'],
        description='Logout user and deactivate account',
        request={
            'application/json': {
                'type': 'object',
                'properties': {},  # Empty since we don't need request body
            }
        },
        responses={
            204: {},
            401: {'description': 'Authentication required'},
            404: {'description': 'User not found'},
        },
        examples=[
            OpenApiExample(
                'Logout Example',
                value={},  # Empty object as we only need the token
                request_only=True
            )
        ]
    )
    def post(self, request):
        try:
            user = request.user
            # Remove tokens from database
            JWTService.remove_tokens(user)
            
            # Set user as inactive
            user.is_active = False
            user.save()
            
            return Response({
                "message": "Logged out successfully"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['User Management'],
        description='Get current logged-in user information',
        responses={
            200: {
                'description': 'Current user information',
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'email': {'type': 'string', 'format': 'email'},
                    'name': {'type': 'string'},
                    'is_active': {'type': 'boolean'},
                    'last_login': {'type': 'string', 'format': 'date-time'},
                }
            },
            401: {'description': 'Authentication required'}
        }
    )
    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'email': user.email,
            'uuid': str(user.id),  # Use user.id (UUID) as the UUID
            'name': user.name,
            'is_verified': user.is_verified,
            'is_active': user.is_active,
            'last_login': user.last_login
        }, status=status.HTTP_200_OK)

class CustomTokenRefreshView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Authentication'],
        description='Refresh access token',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'refresh': {'type': 'string'}
                }
            }
        },
        responses={
            200: {
                'description': 'New access token',
                'type': 'object',
                'properties': {
                    'access': {'type': 'string'}
                }
            }
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'error': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            new_tokens = JWTService.refresh_token(refresh_token)
            return Response(new_tokens, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)

class VerifyEmailView(APIView):
    @extend_schema(
        tags=['User Management'],
        description='Verify user email with verification code',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string', 'format': 'email'},
                    'verification_code': {'type': 'string'},
                },
                'required': ['email', 'verification_code']
            }
        },
        responses={
            204: {},
            400: {'description': 'Invalid or expired verification code'},
            404: {'description': 'User not found'}
        }
    )
    def post(self, request):
        try:
            email = request.data.get('email')
            verification_code = request.data.get('verification_code')

            if not email or not verification_code:
                return Response({
                    'error': 'Email and verification code are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check verification code
            if not user.verification_code or user.verification_code != verification_code:
                return Response({
                    'error': 'Invalid verification code'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if code is expired (1 hour)
            if user.is_token_expired():
                return Response({
                    'error': 'Verification code has expired'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verify user
            user.is_verified = True
            user.is_active = True
            user.verification_code = None  # Clear the code
            user.token_time_to_live = None  # Clear the expiry
            user.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
