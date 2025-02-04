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
        try:
            user = UserService.get_user_by_id(user_id)
            if not user.is_active:
                raise UserInactiveException("The user is already deactivated.")
            user.is_active = False
            user.save()
            return {"message": f"User {user.email} deactivated successfully"}
        except User.DoesNotExist:
            raise UserNotFoundException()
        except Exception as e:
            logger.error(f"Error occurred during deactivation of user {user_id}: {str(e)}")
            raise InvalidUserOperationException(str(e))

    @staticmethod
    def activate_user(user_id):
        try:
            user = User.objects.get(id=user_id)
            
            # Always allow activation
            user.is_active = True
            user.save()
            
            return {
                'success': True,
                'message': 'User activated successfully'
            }
            
        except User.DoesNotExist:
            raise UserNotFoundException(f"User with ID {user_id} not found")

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
        """
        Register a new user with is_active=True by default.
        """
        try:
            # Check if user already exists
            if User.objects.filter(email=user_data['email']).exists():
                raise UserAlreadyExistsException()

            # Create user with is_active=True since we don't need verification
            user = User.objects.create_user(
                email=user_data['email'],
                password=user_data['password'],
                name=user_data.get('name', ''),
                is_active=True  # Set is_active to True since no verification needed
            )
            
            return user

        except Exception as e:
            logger.error(f"Error in user registration: {str(e)}")
            raise InvalidUserOperationException(str(e))


class JWTService:
    @staticmethod
    def create_token(user):
        """
        Create a JWT token for the given user using HS256 algorithm.
        """
        refresh = RefreshToken.for_user(user)
        refresh.algorithm = 'HS256'
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

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


