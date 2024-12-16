# serializers.py
from rest_framework import serializers
from user_management.models.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = '__all__'
        fields = ['email', 'name', 'is_active', 'is_staff', 'rating', 'num_of_usages', 'is_verified']
