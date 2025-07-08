# views.py
from django.contrib.auth import get_user_model, authenticate
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from user_management.services.services import RegistrationService, UserService, JWTService, UserDeletedException
from user_management.serializers.serializers import RegistrationSerializer, UserUpdateSerializer, UserDeactivateSerializer
from core.models import User,EmailVerification
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from django.http import JsonResponse
from user_management.exceptions.custom_exceptions import (
    UserNotFoundException,
    UserInactiveException,
)
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import AuthenticationFailed
from loguru import logger
import sys

class UserDeleteView(APIView):
    permission_classes = [IsAuthenticated]

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

    def delete(self, request, user_id):
        """Delete User"""
        try:
            logger.debug(f"Delete attempt for user ID: {user_id} by user: {request.user.email}")
            
            if request.user.id != user_id:
                logger.warning(f"User {request.user.email} attempted to delete another user's account: {user_id}")
                return Response(
                    {"error": "You can only delete your own account"},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            UserService.delete_user(user_id)
            logger.info(f"Successfully deleted user account: {request.user.email}")
            return Response(status=status.HTTP_204_NO_CONTENT)

        except (UserDeletedException, UserNotFoundException):
            logger.error(f"User not found for deletion. ID: {user_id}")
            return Response({"error": "User Not Found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Unexpected error deleting user {user_id}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        logger.debug(f"Registration attempt with email: {request.data.get('email')}")
        
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user_data = serializer.validated_data
                user_service = RegistrationService()
                user = user_service.register_user(user_data)
                
                logger.info(f"Successfully registered new user: {user.email}")
                return Response({'id': user.id}, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.exception(f"Error during user registration: {str(e)}")
                return Response(
                    {"error": "Registration failed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        logger.warning(f"Invalid registration data: {serializer.errors}")
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
            logger.debug(f"Update attempt for user: {request.user.email}")
            requesting_user = request.user
            
            if requesting_user.is_deleted:
                logger.warning(f"Deleted user attempted to update profile: {requesting_user.email}")
                return Response({
                    "error": "This account has been deleted."
                }, status=status.HTTP_403_FORBIDDEN)
            
            if requesting_user.id != user_id:
                return Response({
                    "error": "You can only update your own information"
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the user to update (should be the same as requesting user)
            user = User.objects.get(id=user_id)
            
            # Prevent updating email or staff status
            if 'email' in request.data or 'is_staff' in request.data:
                return Response(
                    {"error": "Cannot update email, staff status, or active status"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update user data
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Successfully updated user: {user.email}")
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
            
            logger.debug(f"Login attempt for user: {email}")
            
            if not email or not password:
                logger.warning("Login attempt with missing credentials")
                return Response({
                    "error": "Email and password are required."
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = authenticate(request, username=email, password=password)
            
            if user:
                if user.is_deleted:
                    logger.warning(f"Deleted user attempted to login: {email}")
                    return Response({
                        "error": "This account has been deleted."
                    }, status=status.HTTP_403_FORBIDDEN)

                if not user.is_verified:
                    logger.warning(f"Unverified user attempted to login: {email}")
                    return Response({
                        "error": "Please verify your email before logging in."
                    }, status=status.HTTP_403_FORBIDDEN)

                user.is_active = True
                user.save()
                
                tokens = JWTService.create_token(user)
                logger.info(f"Successful login for user: {email}")
                return Response({
                    "refresh": tokens["refresh"],
                    "access": tokens["access"],
                    "message": "Login successful"
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Failed login attempt for user: {email}")
                return Response({
                    "error": "Invalid credentials."
                }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.exception(f"Unexpected error during login for user: {email}")
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
            204: {'description': 'Password reset request received. If the email exists, further instructions will be sent.'}
        }
    )
    def post(self, request):
        email = request.data.get('email')
        logger.debug(f"Password reset request for: {email}")

        if not email:
            logger.warning("Password reset attempt without email")
            return Response(status=status.HTTP_204_NO_CONTENT)

        try:
            user = User.objects.get(email=email)
            if user.is_deleted:
                logger.warning(f"Password reset attempted for deleted account: {email}")
                return Response(status=status.HTTP_204_NO_CONTENT)

            service_response = UserService.initiate_password_reset(email)
            logger.info(f"Password reset email sent to: {email}")

        except Exception as e:
            logger.exception(f"Error in password reset process for {email}")

        return Response(status=status.HTTP_204_NO_CONTENT)


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

            logger.debug(f"Password reset attempt for user: {email}")
            
            userVerify = EmailVerification.objects.get(
                email=email
            )
            

            # Validate all fields are present
            if not all([email, verification_code, new_password, confirm_password]):
                logger.warning(f"Password reset attempt with missing fields for user: {email}")
                return Response({
                    'error': 'All fields are required: email, verification_code, new_password, confirm_password'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if passwords match
            if new_password != confirm_password:
                logger.warning(f"Password mismatch during reset for user: {email}")
                return Response({
                    'error': 'Passwords do not match'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Get user by email
                user = User.objects.get(email=email)

                if user.is_deleted:
                    logger.warning(f"Password reset attempted for deleted account: {email}")
                    return Response({
                        "error": "This account has been deleted."
                    }, status=status.HTTP_403_FORBIDDEN)

                # Verify the code
                if not userVerify.verification_code or userVerify.verification_code != verification_code:
                    logger.warning(f"Invalid verification code used for password reset: {email}")
                    return Response({
                        'error': 'Invalid verification code'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check if code is expired
                if userVerify.is_token_expired():
                    logger.warning(f"Expired verification code used for password reset: {email}")
                    return Response({
                        'error': 'Verification code has expired'
                    }, status=status.HTTP_410_GONE)

                # Reset password
                user.set_password(new_password)
                userVerify.verification_code = None  # Clear the verification code
                userVerify.token_time_to_live = None  # Clear the expiry
                user.is_password_reset_pending = False
                user.save()
                userVerify.save()

                logger.info(f"Successfully reset password for user: {email}")
                return Response({
                    'message': 'Password reset successfully'
                }, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                logger.error(f"Password reset attempted for non-existent user: {email}")
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.exception(f"Unexpected error during password reset for user: {email}")
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
                    'last_login': {'type': 'string', 'format': 'date-time'},
                }
            },
            401: {'description': 'Authentication required'}
        }
    )
    def get(self, request):
try:
    logger.debug(f"Current user info request for: {request.user.email}")
    user = request.user
    
    if user.is_deleted:
        logger.warning(f"Deleted user attempted to access profile: {user.email}")
        return Response({
            "error": "This account has been deleted."
        }, status=status.HTTP_403_FORBIDDEN)

    return Response({
        'id': user.id,
        'email': user.email,
        'uuid': str(user.id),  # Use user.id (UUID) as the UUID
        'name': user.name,
        'is_verified': user.is_verified,
        'is_active': user.is_active,
        'last_login': user.last_login
    }, status=status.HTTP_200_OK)

except Exception as e:
    logger.exception(f"Error retrieving user info for {request.user.email}")
    return Response({
        "error": str(e)
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            logger.debug("Token refresh attempt")

            if not refresh_token:
                logger.warning("Token refresh attempted without refresh token")
                return Response({
                    "error": "Refresh token is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get user from token
            try:
                token = AccessToken(refresh_token)
                user = User.objects.get(id=token['user_id'])
                
                if user.is_deleted:
                    logger.warning(f"Token refresh attempted for deleted account: {user.email}")
                    return Response({
                        "error": "This account has been deleted."
                    }, status.HTTP_403_FORBIDDEN)
                
                new_tokens = JWTService.refresh_token(refresh_token)
                logger.info("Successfully refreshed token")
                return Response(new_tokens, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                logger.error("Token refresh attempted with invalid user ID")
                return Response({
                    "error": "Invalid token"
                }, status.HTTP_401_UNAUTHORIZED)

        except TokenError as e:
            logger.warning(f"Invalid token refresh attempt: {str(e)}")
            return Response({
                "error": "Invalid refresh token"
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.exception("Error in token refresh process")
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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
            logger.debug(f"Email verification attempt for: {email}")

            if not email or not verification_code:
                logger.warning("Email verification attempt with missing data")
                return Response({
                    "error": "Email and verification code are required"
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                userVerify = EmailVerification.objects.get(email=email)
            except EmailVerification.DoesNotExist:
                logger.error(f"No verification record found for email: {email}")
                return Response({
                    "error": "Invalid email or verification code"
                }, status=status.HTTP_400_BAD_REQUEST)
            

            # Check verification code
            if not userVerify.verification_code:
                return Response({
                    'error': 'Please request a verification code'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not userVerify.verification_code == verification_code:
                userVerify.decrement_tries()
                userVerify.save()
                logger.warning(f"Invalid verification code attempt for {email}. Tries left: {userVerify.tries_left}")
                return Response({
                    'error': 'Invalid verification code'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            
            # Check if code is expired (1 hour)
            if userVerify.is_token_expired():
                logger.warning(f"Expired verification code used for {email}")
                return Response({
                    'error': 'Verification code has expired'
                }, status=status.HTTP_400_BAD_REQUEST)


            if userVerify.tries_left <= 0:
                logger.warning(f"No tries left for verification code: {email}")
                userVerify.delete_oldcode()
                return Response({
                    'error': 'No tries left for this verification code. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)

             

            # Verify user
            user=User.objects.get(email=email)
            user.is_verified = True
            userVerify.verification_code = None  # Clear the code
            userVerify.token_time_to_live = None  # Clear the expiry

            user.save()
            userVerify.save()
            logger.info(f"Successfully verified email for user: {email}")
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.exception(f"Error in email verification process for {email}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

        #It should be deleted !!!!!
'''
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['User Management'],
        description='Logout user',
        responses={
            204: {'description': 'Successfully logged out'},
            401: {'description': 'Authentication required'}
        }
    )
    def post(self, request):
        try:
            # Set user as inactive
            user = request.user
            user.is_active = False
            user.save()

            # Remove tokens
            JWTService.remove_tokens(user)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)'''
