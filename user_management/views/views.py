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
from django.http import JsonResponse
from user_management.exceptions.custom_exceptions import (
    UserNotFoundException,
    UserInactiveException,
)
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
from loguru import logger



class UserDeactivateView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['User Management'],
        description='Deactivate your own account.',
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of your account to deactivate'
            ),
        ],
        responses={
            200: {'description': 'User deactivated successfully'},
            400: {'description': 'User is already inactive'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied - Can only deactivate your own account'},
            404: {'description': 'User not found'},
        }
    )
    def patch(self, request, user_id):
        try:
            # Log the incoming request
            requesting_user = request.user
            logger.info(
                f"Received account deactivation request: "
                f"requesting_user_id={requesting_user.id}, target_user_id={user_id}"
            )

            # Check if user is trying to deactivate their own account
            if requesting_user.id != user_id:
                logger.warning(
                    f"Account deactivation failed: Permission denied. "
                    f"Requesting user ID ({requesting_user.id}) does not match target user ID ({user_id})"
                )
                return Response(
                    {"error": "You can only deactivate your own account"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Attempt to deactivate the user
            user = UserService.deactivate_user(user_id)
            logger.info(f"User deactivated successfully: user_id={user_id}")

            # Serialize and return the response
            serializer = UserDeactivateSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except UserNotFoundException:
            logger.warning(f"Account deactivation failed: User not found for user_id={user_id}")
            return Response(
                {'detail': 'User not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except UserInactiveException as e:
            logger.warning(f"Account deactivation failed: User is already inactive for user_id={user_id}")
            return Response(
                {'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error during account deactivation for user_id={user_id}: {e}")
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
        # Log the incoming request data
        logger.info(f"Received registration request: {request.data}")

        # Validate the request data
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            # Log validation errors
            logger.warning(f"Validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Log successful validation
        logger.debug("Request data validated successfully")

        try:
            # Register the user
            user_data = serializer.validated_data
            user_service = RegistrationService()
            user = user_service.register_user(user_data)

            # Log successful user registration
            logger.info(f"User registered successfully: email={user_data['email']}, name={user_data['name']}")

            # Return success response
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Log any unexpected errors during registration
            logger.error(f"Error during user registration: {e}")
            return Response(
                {"error": "An error occurred during registration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    


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
            200: {
                'description': 'User updated successfully',
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'name': {'type': 'string'},
                    'email': {'type': 'string', 'format': 'email'}
                }
            },
            400: {'description': 'Bad request - Invalid data or incorrect current password'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'User not found'}
        }
    )
    def patch(self, request, user_id):
        try:
            # Log the incoming request
            requesting_user = request.user
            logger.info(
                f"Received user update request: "
                f"requesting_user_id={requesting_user.id}, target_user_id={user_id}"
            )

            # Check if user is trying to update their own information
            if requesting_user.id != user_id:
                logger.warning(
                    f"User update failed: Permission denied. "
                    f"Requesting user ID ({requesting_user.id}) does not match target user ID ({user_id})"
                )
                return Response(
                    {"error": "You can only update your own information"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get the user to update (should be the same as requesting user)
            user = User.objects.get(id=user_id)
            logger.debug(f"User found: user_id={user_id}")

            # Prevent updating email or staff status
            if 'email' in request.data or 'is_staff' in request.data or 'is_active' in request.data:
                logger.warning(
                    f"User update failed: Attempted to update restricted fields. "
                    f"Request data: {request.data}"
                )
                return Response(
                    {"error": "Cannot update email, staff status, or active status"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update user data
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User updated successfully: user_id={user_id}")
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            # Log validation errors
            logger.warning(f"User update failed: Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except User.DoesNotExist:
            logger.warning(f"User update failed: User not found for user_id={user_id}")
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error during user update for user_id={user_id}: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ActivateUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['User Management'],
        description='Activate your own account.',
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of your account to activate'
            ),
        ],
        responses={
            200: {'description': 'User activated successfully'},
            400: {'description': 'User is already active'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied - Can only activate your own account'},
            404: {'description': 'User not found'},
        }
    )
    def patch(self, request, user_id):
        try:
            # Log the incoming request
            logger.info(
                f"Received account activation request: "
                f"request_user_id={request.user.id}, target_user_id={user_id}"
            )

            # Check if user is trying to activate their own account
            if request.user.id != user_id:
                logger.warning(
                    f"Account activation failed: Permission denied. "
                    f"Request user ID ({request.user.id}) does not match target user ID ({user_id})"
                )
                return Response(
                    {"error": "You can only activate your own account"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Try to activate the user
            service_response = UserService.activate_user(user_id)
            
            if service_response['success']:
                logger.info(f"User activated successfully: user_id={user_id}")
                return Response(service_response, status=status.HTTP_200_OK)
            else:
                logger.warning(f"User activation failed: user_id={user_id}, reason={service_response.get('message')}")
                return Response(service_response, status=status.HTTP_400_BAD_REQUEST)
            
        except UserNotFoundException as e:
            logger.warning(f"Account activation failed: User not found for user_id={user_id}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error during account activation for user_id={user_id}: {e}")
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
            400: {'description': 'Bad request'},
            401: {'description': 'Invalid credentials'},
            403: {'description': 'Email not verified'},
            404: {'description': 'User not found'}
        }
    )
    def post(self, request):
        try:
            # Log the incoming request data
            logger.info(f"Received login request: email={request.data.get('email')}")

            email = request.data.get('email')
            password = request.data.get('password')
            
            # Validate required fields
            if not email or not password:
                logger.warning("Login failed: Email and password are required")
                return Response({
                    "error": "Email and password are required."
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Authenticate the user
            user = authenticate(request, username=email, password=password)
            
            if user:
                # Log successful authentication
                logger.debug(f"User authenticated: email={email}")

                # Check if email is verified
                if not user.is_verified:
                    logger.warning(f"Login failed: Email not verified for user={email}")
                    return Response({
                        "error": "Please verify your email before logging in. Check your inbox for the verification code."
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Set user as active when logging in
                user.is_active = True
                user.save()

                # Generate JWT tokens
                tokens = JWTService.create_token(user)
                logger.info(f"JWT tokens generated for user={email}")

                # Log successful login
                logger.info(f"Login successful: email={email}")

                return Response({
                    "refresh": tokens["refresh"],
                    "access": tokens["access"],
                    "message": "Login successful"
                }, status=status.HTTP_200_OK)
            else:
                # Log invalid credentials
                logger.warning(f"Login failed: Invalid credentials for email={email}")
                return Response({
                    "error": "Invalid credentials."
                }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error during login: {e}")
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
        try:
            # Log the incoming request
            email = request.data.get('email')
            logger.info(f"Received forgot password request: email={email}")

            # Validate required field
            if not email:
                logger.warning("Forgot password failed: Email is required")
                return Response({
                    'error': 'Email is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Initiate password reset
            service_response = UserService.initiate_password_reset(email)
            logger.info(f"Password reset initiated successfully: email={email}")

            return Response(service_response, status=status.HTTP_200_OK)

        except ValueError as ve:
            # Log validation errors
            logger.warning(f"Forgot password failed: {ve}")
            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error during forgot password for email={email}: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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
            # Log the incoming request
            logger.info(f"Received password reset request: email={request.data.get('email')}")

            # Get all required fields
            email = request.data.get('email')
            verification_code = request.data.get('verification_code')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')

            # Validate all fields are present
            if not all([email, verification_code, new_password, confirm_password]):
                logger.warning("Password reset failed: All fields are required")
                return Response({
                    'error': 'All fields are required: email, verification_code, new_password, confirm_password'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if passwords match
            if new_password != confirm_password:
                logger.warning(f"Password reset failed: Passwords do not match for email={email}")
                return Response({
                    'error': 'Passwords do not match'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Get user by email
                user = User.objects.get(email=email)
                logger.debug(f"User found: email={email}")

                # Verify the code
                if not user.verification_code or user.verification_code != verification_code:
                    logger.warning(f"Password reset failed: Invalid verification code for email={email}")
                    return Response({
                        'error': 'Invalid verification code'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check if code is expired
                if user.is_token_expired():
                    logger.warning(f"Password reset failed: Verification code expired for email={email}")
                    return Response({
                        'error': 'Verification code has expired'
                    }, status=status.HTTP_410_GONE)

                # Reset password
                user.set_password(new_password)
                user.verification_code = None  # Clear the verification code
                user.token_time_to_live = None  # Clear the expiry
                user.is_password_reset_pending = False
                user.save()

                # Log successful password reset
                logger.info(f"Password reset successfully: email={email}")

                return Response({
                    'message': 'Password reset successfully'
                }, status=status.HTTP_200_OK)

            except User.DoesNotExist:
                logger.warning(f"Password reset failed: User not found for email={email}")
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error during password reset for email={email}: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
          


          
##Bet-30##
def user_view(request):
    #A function that handles requests to /api/user
    #I still don't know what specific data we need, so meanwhile I used these, but I can replace it later with actual database queries

    user_data = {
        'username': 'example_user',
        'email': 'user@gmail.com'
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
            # Log the incoming request
            user = request.user
            logger.info(f"Received logout request: user_id={user.id}, email={user.email}")

            # Remove tokens from database
            JWTService.remove_tokens(user)
            logger.debug(f"Tokens removed for user_id={user.id}")

            # Set user as inactive
            user.is_active = False
            user.save()
            logger.info(f"User deactivated: user_id={user.id}")

            return Response({
                "message": "Logged out successfully"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error during logout for user_id={user.id}: {e}")
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from loguru import logger
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

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
        try:
            # Log the incoming request
            user = request.user
            logger.info(f"Received request for current user information: user_id={user.id}")

            # Return user information
            logger.debug(f"Retrieved current user information: user_id={user.id}, email={user.email}")
            return Response({
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'is_active': user.is_active,
                'last_login': user.last_login
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error retrieving current user information: {e}")
            return Response({
                'error': str(e)
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
            # Log the incoming request
            logger.info("Received token refresh request")

            refresh_token = request.data.get('refresh')

            # Validate required field
            if not refresh_token:
                logger.warning("Token refresh failed: Refresh token is required")
                return Response({
                    'error': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Refresh the token
            new_tokens = JWTService.refresh_token(refresh_token)
            logger.info("New access token generated successfully")

            return Response(new_tokens, status=status.HTTP_200_OK)

        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error during token refresh: {e}")
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
            200: {'description': 'Email verified successfully'},
            400: {'description': 'Invalid or expired verification code'},
            404: {'description': 'User not found'}
        }
    )
    def post(self, request):
        try:
            # Log the incoming request data
            logger.info(f"Received email verification request: email={request.data.get('email')}")

            email = request.data.get('email')
            verification_code = request.data.get('verification_code')

            # Validate required fields
            if not email or not verification_code:
                logger.warning("Email verification failed: Email and verification code are required")
                return Response({
                    'error': 'Email and verification code are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Look up the user
                user = User.objects.get(email=email)
                logger.debug(f"User found: email={email}")
            except User.DoesNotExist:
                # Log user not found
                logger.warning(f"Email verification failed: User not found for email={email}")
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check verification code
            if not user.verification_code or user.verification_code != verification_code:
                logger.warning(f"Email verification failed: Invalid verification code for email={email}")
                return Response({
                    'error': 'Invalid verification code'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if code is expired
            if user.is_token_expired():
                logger.warning(f"Email verification failed: Verification code expired for email={email}")
                return Response({
                    'error': 'Verification code has expired'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verify user
            user.is_verified = True
            user.is_active = True
            user.verification_code = None  # Clear the code
            user.token_time_to_live = None  # Clear the expiry
            user.save()

            # Log successful email verification
            logger.info(f"Email verified successfully: email={email}")

            return Response({
                'message': 'Email verified successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error during email verification: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)