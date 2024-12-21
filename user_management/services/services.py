from django.contrib.auth import get_user_model

class UserService:
    @staticmethod
    def deactivate_user(user_id):
        try:
            User = get_user_model()
            user = User.objects.get(id=user_id)
            if user.is_active:
                user.is_active = False
                user.save()
                return {"message": f"User {user.email} deactivated success"}
            else:
                return {"message": f"User {user.email} is already deactivated"}
        except User.DoesNotExist:
            raise ValueError('User not found.')
        except Exception as e:
            raise ValueError(f"An error occurred: {str(e)}")

