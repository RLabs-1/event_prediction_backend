# serializers.py
from rest_framework import serializers
from user_management.models.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = '__all__'
        fields = ['email', 'name', 'is_active', 'is_staff', 'rating', 'num_of_usages', 'is_verified']

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'name', 'password']  

    def create(self, validated_data):
       
        user = User(
            email=validated_data['email'],
            name=validated_data['name'],
            is_active=True,  
            is_staff=False
        )
        user.set_password(validated_data['password'])  
        user.save()
        return user