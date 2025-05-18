    # from rest_framework import serializers
    # from core.models import EventSystemConfiguration
    #
    # class EventSystemConfigurationSerializer(serializers.ModelSerializer):
    #     class Meta:
    #         model = EventSystemConfiguration
    #         fields = [
    #             'id',
    #             'event_system',
    #             'learning_time_minutes',
    #             'region',
    #             'timezone',
    #             'logs_pattern',
    #         ]
    #         read_only_fields = ['id', 'event_system']



# user_management/serializers/eventsystem_serializers.py

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
