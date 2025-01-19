# serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from core.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = '__all__'
        fields = ['email', 'name', 'is_active', 'is_staff', 'rating', 'num_of_usages', 'is_verified']




User = get_user_model()

class UserDeactivateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_active']

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
        # user.set_password(validated_data['password'])
        # user.save(using=self._db)
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating User details"""

    class Meta:
        model = User
        fields = ['email', 'password', 'name', 'is_active', 'is_staff', 'rating', 'num_of_usages', 'is_verified']
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 5
            }
        }
        read_only_fields = ['is_active', 'is_staff', 'rating', 'num_of_usages', 'is_verified']

    def update(self, instance, validated_data):
        """Update a user instance"""

        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user

