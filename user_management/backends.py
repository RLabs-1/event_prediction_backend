from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.exceptions import ValidationError


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Try to fetch the user by email or username
            user = UserModel.objects.get(
                Q(username=username) | Q(email=username)
            )
            if user.check_password(password):
                return user
        #Handling user-related errors appropriately
        except UserModel.DoesNotExist:
            return None
        except ValidationError as ve:
            raise ValidationError(f"Validation error: {str(ve)}")
        except Exception as e:
            raise ValidationError(f"Unexpected error during authentication: {str(e)}")
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None 