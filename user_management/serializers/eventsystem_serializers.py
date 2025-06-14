from rest_framework import serializers
from core.models import EventSystem, FileReference, User  # Adjust imports if User is custom or from another app

class EventSystemConfigurationSerializer(serializers.ModelSerializer):
    file_objects = serializers.PrimaryKeyRelatedField(
        queryset=FileReference.objects.all(),
        many=True,
        required=False
    )
    users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = EventSystem
        fields = ['name', 'status', 'file_objects', 'users']
        extra_kwargs = {
            'name': {'required': False},
            'status': {'required': False},
        }
