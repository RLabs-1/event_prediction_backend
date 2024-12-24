from user_management.models.models import User
from django.core.exceptions import ObjectDoesNotExist

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
                return {"message": f"User {user.email} activated successfully."}
            return {"message": "User is already active."}
        except ObjectDoesNotExist:
            return {"message": "User not found!."}




