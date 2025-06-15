from rest_framework import serializers
from core.models import EventSystemConfiguration, LogsPattern


class EventSystemConfigurationPatchSerializer(serializers.ModelSerializer):
    logs_pattern_id = serializers.IntegerField(required=False)

    class Meta:
        model = EventSystemConfiguration
        fields = ['learning_time_minutes', 'region', 'timezone', 'logs_pattern_id']
        extra_kwargs = {
            'learning_time_minutes': {'required': False},
            'region': {'required': False},
            'timezone': {'required': False},
        }

    def validate_learning_time_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError("Learning time must be positive")
        return value

    def validate_logs_pattern_id(self, value):
        if not LogsPattern.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"LogsPattern with id {value} does not exist.")
        return value

    def update(self, instance, validated_data):
        # Handle logs_pattern_id
        if 'logs_pattern_id' in validated_data:
            logs_pattern_id = validated_data.pop('logs_pattern_id')
            instance.logs_pattern_id = logs_pattern_id

        # Update other fields and save
        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.save()
        return instance