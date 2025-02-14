from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPException
import random
import logging
from datetime import timedelta
from django.utils import timezone
from user_management.exceptions.custom_exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    UserInactiveException,
    InvalidUserOperationException,
)
from .email_service import EmailService
from core.models import UserToken

# Set up logger to track errors in User Management
logger = logging.getLogger(__name__)

User = get_user_model()  # Ensure we are using the correct User model

# Custom Exception Definitions
class UserNotFoundException(Exception):
    """Raised when a user is not found."""
    pass

class UserInactiveException(Exception):
    """Raised when attempting to deactivate an already inactive user."""
    pass

class InvalidUserOperationException(Exception):
    """Raised for unexpected errors or invalid operations."""
    pass

class UserService:
    @staticmethod
    def get_user_by_id(user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} not found.")
            raise UserNotFoundException()

    @staticmethod
    def deactivate_user(user_id):
        """Deactivate a user account"""
        try:
            user = User.objects.get(id=user_id)
            if not user.valid_account:
                raise UserInactiveException("User is already inactive")
            user.valid_account = False
            user.save()
            return user
        except User.DoesNotExist:
            raise UserNotFoundException()

    @staticmethod
    def activate_user(user_id):
        """Activate a user account"""
        try:
            user = User.objects.get(id=user_id)
            if user.valid_account:
                return {
                    "message": "User is already active",
                    "success": False
                }
            user.valid_account = True
            user.save()
            return {
                "message": "User activated successfully",
                "success": True
            }
        except User.DoesNotExist:
            raise UserNotFoundException()

    @staticmethod
    def verify_code(email, verification_code):
        """
        Verify if the provided code matches the stored code for the user
        and hasn't expired
        """
        try:
            user = User.objects.get(email=email)
            stored_code = user.verification_code
            code_timestamp = user.token_time_to_live

            # Check if code exists and matches
            if not stored_code or stored_code != verification_code:
                return False

            # Check if code has expired (e.g., after 15 minutes)
            if not code_timestamp or (timezone.now() - code_timestamp).total_seconds() > 900:  # 15 minutes
                return False

            return True

        except User.DoesNotExist:
            return False

    @staticmethod
    def reset_password(email, verification_code, new_password, confirm_password):
        try:
            # 1. Verify passwords match
            if new_password != confirm_password:
                raise ValueError("Passwords do not match")
                
            # 2. Validate password strength
            if not UserService.is_password_strong(new_password):
                raise ValueError("Password must be at least 8 characters long and contain uppercase, lowercase, numbers and special characters")
                
            # 3. Verify code
            if not UserService.verify_code(email, verification_code):
                raise ValueError("Invalid or expired verification code")
                
            # 4. Update password
            user = User.objects.get(email=email)
            user.set_password(new_password)
            # Clear the verification code after successful reset
            user.verification_code = None
            user.token_time_to_live = None
            user.save()
            
            return {
                "message": "Password reset successfully"
            }
            
        except User.DoesNotExist:
            raise ValueError("No user found with this email address")

    @staticmethod
    def initiate_password_reset(email):
        try:
            # Find user
            user = User.objects.get(email=email)
            
            # Generate verification code
            verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Log the code (for debugging)
            print(f"Generated code for {email}: {verification_code}")
            
            # Save verification code and set expiry
            user.verification_code = verification_code
            user.token_time_to_live = timezone.now()
            user.save()
            
            # Log stored code (for debugging)
            stored_user = User.objects.get(email=email)
            print(f"Stored code in DB: {stored_user.verification_code}")
            
            # Send email with verification code
            EmailService.send_password_reset_email(
                email=email,
                verification_code=verification_code
            )
            
            return {
                "message": "Password reset email sent successfully"
            }
            
        except User.DoesNotExist:
            raise ValueError("No user found with this email address")

    @staticmethod
    def is_password_strong(password):
       """
       Simple password validation
      - At least 4 characters long
       """
       return len(password) >= 4


class RegistrationService:
    def register_user(self, user_data):
        """Register a new user and send verification email"""
        try:
            # Check if user already exists
            if User.objects.filter(email=user_data['email']).exists():
                raise UserAlreadyExistsException()

            # Create user with is_active=False until verified
            user = User.objects.create_user(
                email=user_data['email'],
                password=user_data['password'],
                name=user_data.get('name', ''),
                is_active=False,
                is_verified=False
            )

            # Send welcome email with verification code
            try:
                verification_code = EmailService.send_email(user.email)
                user.verification_code = verification_code
                user.token_time_to_live = timezone.now()
                user.save()
            except Exception as e:
                logger.error(f"Error sending verification email: {str(e)}")
                # Continue with registration even if email fails

            return user

        except Exception as e:
            logger.error(f"Error in user registration: {str(e)}")
            raise InvalidUserOperationException(str(e))


class JWTService:
    @staticmethod
    def create_token(user):
        """Create and store JWT token for the user"""
        try:
            refresh = RefreshToken.for_user(user)
            refresh.algorithm = 'HS256'
            
            # Create token pair
            tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            
            # Store or update tokens in database
            try:
                UserToken.objects.update_or_create(
                    user=user,
                    defaults={
                        'access_token': tokens['access'],
                        'refresh_token': tokens['refresh']
                    }
                )
            except Exception as e:
                logger.error(f"Error storing tokens in database: {str(e)}")
                # Continue even if database storage fails
                
            return tokens
            
        except Exception as e:
            logger.error(f"Error creating tokens: {str(e)}")
            raise InvalidUserOperationException("Error creating authentication tokens")

    @staticmethod
    def refresh_token(refresh_token_str):
        """Refresh access token and update in database"""
        try:
            refresh = RefreshToken(refresh_token_str)
            user_id = refresh.payload.get('user_id')
            user = User.objects.get(id=user_id)
            
            # Generate new access token
            new_access_token = str(refresh.access_token)
            
            # Update in database
            try:
                user_token = UserToken.objects.get(user=user)
                user_token.access_token = new_access_token
                user_token.save()
            except UserToken.DoesNotExist:
                # Create new token record if it doesn't exist
                UserToken.objects.create(
                    user=user,
                    access_token=new_access_token,
                    refresh_token=refresh_token_str
                )
            
            return {
                'access': new_access_token
            }
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise InvalidToken(f"Invalid refresh token")

    @staticmethod
    def remove_tokens(user):
        """Remove user tokens from database"""
        try:
            UserToken.objects.filter(user=user).delete()
        except Exception as e:
            logger.error(f"Error removing tokens: {str(e)}")
            # Continue even if token removal fails

    @staticmethod
    def get_user(token):
        """
        Get the user from the given token.
        """
        try:
            # First, try to decode as an access token
            validated_token = AccessToken(token)
            user_id = validated_token.get('user_id')  # Use `.get()` to avoid KeyError
            if not user_id:
                raise InvalidToken("Token is missing user_id claim.")
            return User.objects.get(id=user_id)
        except (TokenError, InvalidToken, User.DoesNotExist):
            try:
                # If it's not an access token, try as a refresh token
                validated_token = RefreshToken(token)
                user_id = validated_token.get('user_id')
                if not user_id:
                    raise InvalidToken("Token is missing user_id claim.")
                return User.objects.get(id=user_id)
            except (TokenError, InvalidToken, User.DoesNotExist):
                return None


