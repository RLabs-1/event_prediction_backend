from django.contrib.auth import get_user_model
from user_management.models.models import User
from core.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPException
import logging


# Set up logger in order to track Errors in User Management
logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    def deactivate_user(user_id):
        try:
            User = get_user_model()
            user = User.objects.get(id=user_id)
            if user.is_active:
                user.is_active = False
                user.save()
                return {"message": f"User {user.email} deactivated successfully"}
            else:
                return {"message": f"User {user.email} is already deactivated"}
        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} not found during deactivation.")
            raise ValueError('User not found.')
        except Exception as e:
            logger.error(f"Error occurred during deactivation of user {user_id}: {str(e)}")
            raise ValueError(f"An error occurred: {str(e)}")



class UserService:
    @staticmethod
    def activate_user(user_id):
        """
        Activates the user account by setting the field of is_active to True.
        """
        try:
            user = User.objects.get(id=user_id)
            if not user.is_active:
                user.is_active = True
                user.save()
                return {
                    'success': True,
                    'message': 'User activated successfully'
                }
            return {
                'success': False,
                'message': 'User is already active'
            }
        except User.DoesNotExist:
            logger.error(f"User with ID {user_id} not found during activation.")
            return {
                'success': False,
                'message': 'User not found'
            }
        except Exception as e:
            logger.error(f"Error occurred during activation of user {user_id}: {str(e)}")
            return {
                'success': False,
                'message': f"Unexpected error: {str(e)}"
            }


    @staticmethod
    def initiate_password_reset(email):
        try:
            user = User.objects.get(email=email)
            
            # Generate 6-digit code
            verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Set expiry to 1 hour from now
            expiry_time = timezone.now() + timedelta(hours=1)
            
            # Update user
            user.is_password_reset_pending = True
            user.password_reset_code = verification_code
            user.password_reset_code_expiry = expiry_time
            user.save()
            
            # Send email
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

        # Including errors for email sending issues:
        except User.DoesNotExist:
            logger.error(f"User with email {email} not found during password reset.")
            raise ValueError("No user found with this email address.")
        except SMTPException as e:
            logger.error(f"Error sending password reset email to {email}: {str(e)}")
            raise ValueError(f"Error sending email: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during password reset for {email}: {str(e)}")
            raise ValueError(f"Unexpected error during password reset: {str(e)}")



class RegistrationService:
    @staticmethod
    def register_user(validated_data):

        user = User(
            email=validated_data['email'],
            name=validated_data['name'],
            is_active=True,
            is_staff=False
        )
        user.set_password(validated_data['password'])
        user.save()

        return user


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
            user_id = validated_token['user_id']
            return User.objects.get(id=user_id)
        except (TokenError, InvalidToken, User.DoesNotExist):
            try:
                # If it's not an access token, try as a refresh token
                validated_token = RefreshToken(token)
                user_id = validated_token['user_id']
                return User.objects.get(id=user_id)
            except (TokenError, InvalidToken, User.DoesNotExist):
                return None


