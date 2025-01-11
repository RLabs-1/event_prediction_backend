from django.shortcuts import get_object_or_404
from user_management.models import EventSystem, FileReference
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


class EventSystemFileService:
    @staticmethod
    def delete_file(event_system_id, file_id):
        event_system = get_object_or_404(EventSystem, uuid=event_system_id)
        file_reference = get_object_or_404(FileReference, uuid=file_id, event_system=event_system)
        file_reference.delete()


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
            raise ValueError('User not found.')

    @staticmethod
    def activate_user(user_id):
        try:
            user = get_user_model().objects.get(id=user_id)
            if not user.is_active:
                user.is_active = True
                user.save()
                return {'success': True, 'message': 'User activated successfully'}
            return {'success': False, 'message': 'User is already active'}
        except User.DoesNotExist:
            return {'success': False, 'message': 'User not found'}

    @staticmethod
    def initiate_password_reset(email):
        try:
            user = get_user_model().objects.get(email=email)
            verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            expiry_time = timezone.now() + timedelta(hours=1)
            user.is_password_reset_pending = True
            user.password_reset_code = verification_code
            user.password_reset_code_expiry = expiry_time
            user.save()
            
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
            return {'success': True, 'message': 'Password reset verification code sent successfully'}
        except User.DoesNotExist:
            return {'success': False, 'message': 'No user found with this email address'}


class RegistrationService:
    @staticmethod
    def register_user(validated_data):
        User = get_user_model()
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
        refresh = RefreshToken.for_user(user)
        refresh.algorithm = 'HS256'
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    def get_user(token):
        try:
            validated_token = AccessToken(token)
            user_id = validated_token['user_id']
            return get_user_model().objects.get(id=user_id)
        except (TokenError, InvalidToken, ObjectDoesNotExist):
            try:
                validated_token = RefreshToken(token)
                user_id = validated_token['user_id']
                return get_user_model().objects.get(id=user_id)
            except (TokenError, InvalidToken, ObjectDoesNotExist):
                return None
