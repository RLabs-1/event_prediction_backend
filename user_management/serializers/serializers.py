# serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from core.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = '__all__'
        fields = ['email', 'name', 'is_staff', 'rating', 'num_of_usages', 'is_verified']




User = get_user_model()

class UserDeactivateSerializer(serializers.ModelSerializer):
    pass
    # class Meta:
    #     model = User

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'name', 'password']

    def create(self, validated_data):

        user = User(
            email=validated_data['email'],
            name=validated_data['name'],
            is_staff=False
        )
        # user.set_password(validated_data['password'])
        # user.save(using=self._db)
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating User details"""
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 
            'name', 
            'email',
            'is_staff', 
            'rating', 
            'num_of_usages',
            'current_password',
            'new_password'
        ]
        read_only_fields = [
            'id', 
            'email',  # Can't update email
            'is_staff',  # Can't update staff status
            'rating',  # Read-only field
            'num_of_usages'  # Read-only field
        ]

    def validate(self, attrs):
        # Check if trying to update password
        if 'new_password' in attrs and not attrs.get('current_password'):
            raise serializers.ValidationError({
                'current_password': 'Current password is required to set new password'
            })
        
        # Prevent setting is_staff to True
        if attrs.get('is_staff'):
            raise serializers.ValidationError({
                'is_staff': 'Cannot set staff status'
            })
        return attrs

    def update(self, instance, validated_data):
        """Update a user instance"""
        current_password = validated_data.pop('current_password', None)
        new_password = validated_data.pop('new_password', None)

        # Handle password update
        if new_password:
            if not instance.check_password(current_password):
                raise serializers.ValidationError({
                    'current_password': 'Current password is incorrect'
                })
            instance.set_password(new_password)

        # Update other fields
        for attr, value in validated_data.items():
            if attr != 'email' and attr != 'is_staff':  # Extra safety check
                setattr(instance, attr, value)
        
        instance.save()
        return instance

