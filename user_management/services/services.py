# services.py
from user_management.models.models import User

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
