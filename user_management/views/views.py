# views.py
from django.contrib.auth import get_user_model, authenticate
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from user_management.services.services import RegistrationService, UserService, JWTService
from user_management.serializers.serializers import RegistrationSerializer, UserUpdateSerializer, UserDeactivateSerializer
from user_management.models.models import User
from core.models import User
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from django.shortcuts import render
from django.http import JsonResponse
import json
from ..services.email_service import EmailService
from user_management.exceptions.custom_exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    UserInactiveException,
    InvalidUserOperationException,
)
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone


class UserDeactivateView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['User Management'],
        description='Deactivate a user account. Only superusers can deactivate user accounts.',
        parameters=[
            OpenApiParameter(
                name='userId',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID of the user to deactivate'
            ),
        ],
        responses={
            200: {'description': 'User deactivated successfully'},
            400: {'description': 'User is already inactive'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied - Superuser access required'},
            404: {'description': 'User not found'},
        }
    )
    def patch(self, request, userId):
        try:
            # Check if user is superuser
            if not request.user.is_superuser:
                return Response(
                    {"error": "Only superusers can deactivate user accounts"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Attempt to deactivate the user
            user = UserService.deactivate_user(userId)
            serializer = UserDeactivateSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except UserNotFoundException:
            return Response(
                {'detail': 'User not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except UserInactiveException as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
                    'email': {'type': 'string'},
                    'name': {'type': 'string'},
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

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['User Management'],
        description='Update user information (except email and staff status). Users can only update their own information.',
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID of the user to update (must be your own ID unless you are a superuser)'
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
            200: {
                'description': 'User updated successfully',
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'email': {'type': 'string', 'format': 'email'}
                }
            },
            400: {'description': 'Bad request - Invalid data or incorrect current password'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied - Can only update your own information'},
            404: {'description': 'User not found'},
        }
    )
    def patch(self, request, user_id):
        try:
            # Get the requesting user
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
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class ActivateUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['User Management'],
        description='Activate a user account. Only superusers can activate user accounts.',
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID of the user to activate'
            ),
        ],
        responses={
            200: {'description': 'User activated successfully'},
            400: {'description': 'User is already active'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied - Superuser access required'},
            404: {'description': 'User not found'},
        }
    )
    def patch(self, request, user_id):
        """
        Activates a deactivated user account.
        Only superusers can activate accounts.
        """
        try:
            # Check if user is superuser
            if not request.user.is_superuser:
                return Response(
                    {"error": "Only superusers can activate user accounts"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Try to activate the user
            service_response = UserService.activate_user(user_id)
            
            if service_response['success']:
                return Response(service_response, status=status.HTTP_200_OK)
            else:
                return Response(service_response, status=status.HTTP_400_BAD_REQUEST)
            
        except UserNotFoundException as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            400: {'description': 'Bad request - Another user is logged in'},
            401: {'description': 'Invalid credentials'},
            404: {'description': 'User not found'}
        },
        examples=[
            OpenApiExample(
                'Login Example',
                value={
                    'email': 'user@gmail.com',
                    'password': 'password'
                },
                request_only=True
            )
        ]
    )
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({
                "error": "Email and password are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            
            # Check if user is already active/logged in, skip for superusers
            if user.is_active and not user.is_superuser:
                return Response({
                    "error": "Another user is already logged in. Please logout first.",
                    "status": "active"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Authenticate user
            if user.check_password(password):
                # Update last_login timestamp
                user.last_login = timezone.now()
                
                # Activate user and save changes
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
                    "error": "Incorrect password."
                }, status=status.HTTP_401_UNAUTHORIZED)
                
        except User.DoesNotExist:
            return Response({
                "error": "No account found with this email address."
            }, status=status.HTTP_404_NOT_FOUND)

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
        description='Reset password using verification code',
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
            404: {'description': 'User not found'}
        }
    )
    def post(self, request):
        email = request.data.get('email')
        verification_code = request.data.get('verification_code')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        # Make sure all required fields are present
        if not all([email, verification_code, new_password, confirm_password]):
            return Response({
                'error': 'All fields are required: email, verification_code, new_password, confirm_password'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            service_response = UserService.reset_password(
                email, 
                verification_code, 
                new_password, 
                confirm_password
            )
            return Response(service_response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

          


          
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
            200: {
                'description': 'Logout successful',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                }
            },
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
            user.is_active = False
            user.save()
            
            return Response({
                "message": "Logged out successfully and account deactivated"
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
            'name': user.name,
            'is_active': user.is_active,
            'last_login': user.last_login
        }, status=status.HTTP_200_OK)
