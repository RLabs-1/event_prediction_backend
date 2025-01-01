

from user_management.models.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


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
                return {"message": f"User {user_id} activated successfully."}
            return {"message": "User is already active."}
        except ObjectDoesNotExist:
            return {"message": "User not found!."}







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


