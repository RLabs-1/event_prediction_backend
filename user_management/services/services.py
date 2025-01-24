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
            user = UserService.get_user_by_id(user_id)
            if user.is_active:
                return {
                    'success': False,
                    'message': 'User is already active',
                }
            user.is_active = True
            user.save()
            return {
                'success': True,
                'message': 'User activated successfully',
            }
        except User.DoesNotExist:
            raise UserNotFoundException()
        except Exception as e:
            logger.error(f"Error occurred during activation of user {user_id}: {str(e)}")
            raise InvalidUserOperationException(str(e))

    @staticmethod
    def initiate_password_reset(email):
        try:
            user = User.objects.get(email=email)

            # Check if a password reset is already in progress
            if user.is_password_reset_pending and user.password_reset_code_expiry > timezone.now():
                raise InvalidUserOperationException("A password reset is already in progress.")

            # Generate a 6-digit verification code
            verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            # Set expiry to 1 hour from now
            expiry_time = timezone.now() + timedelta(hours=1)

            # Update user details
            user.is_password_reset_pending = True
            user.password_reset_code = verification_code
            user.password_reset_code_expiry = expiry_time
            user.save()

            # Send email with the reset code
            reset_url = f"{settings.DOMAIN_URL}/api/user/reset-forgot-password"
            email_body = f"""
            Your password reset verification code is: {verification_code}

            Please visit {reset_url} to reset your password.

            This code will expire in 1 hour.
            """
            send_mail(
                'Password Reset Request',
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            return {
                'success': True,
                'message': 'Password reset verification code sent successfully'
            }
        except User.DoesNotExist:
            logger.error(f"User with email {email} not found during password reset.")
            raise UserNotFoundException()
        except SMTPException as e:
            logger.error(f"Error sending password reset email to {email}: {str(e)}")
            raise InvalidUserOperationException(f"Error sending email: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during password reset for {email}: {str(e)}")
            raise InvalidUserOperationException(str(e))


class RegistrationService:
    @staticmethod
    def register_user(validated_data):
        try:
            user = User(
                email=validated_data['email'],
                name=validated_data['name'],
                is_active=True,
                is_staff=False
            )
            user.set_password(validated_data['password'])
            user.save()
            return user
        except Exception as e:
            logger.error(f"Error occurred during user registration: {str(e)}")
            raise InvalidUserOperationException("Error during user registration.")

    @staticmethod
    def verify_email(email, verification_code):
        """
        Verify the user's email using the provided verification code.
        """
        try:
            user = User.objects.get(email=email)

            # Simulate the verification process; ideally, the code is stored in the DB or sent to the user's email
            if verification_code == 'expected_code':  # Replace with actual verification logic
                user.is_verified = True
                user.save()
                return {"message": f"Email for {email} has been successfully verified."}
            else:
                return {"message": "Invalid verification code."}
        except User.DoesNotExist:
            return {"message": "User not found!"}


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


