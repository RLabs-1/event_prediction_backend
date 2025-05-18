from rest_framework import serializers
from core.models import EventSystem, FileReference, LogsPattern, EventSystemConfiguration

class EventSystemCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = EventSystem
        fields = ['id', 'name']


class FileReferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for the FileReference model.
    Handles serialization and deserialization of FileReference instances.
    """

    storage_provider = serializers.SerializerMethodField()
    upload_status = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = FileReference
        fields = '__all__'  # Include all fields

    def get_storage_provider(self, obj):
        return obj.get_storage_provider_display()

    def get_upload_status(self, obj):
        return obj.get_upload_status_display()

    def get_file_type(self, obj):
        return obj.get_file_type_display()


class EventSystemNameUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSystem
        fields = ['name']  # Only allow updating the name field        

class CustomPatternSerializer(serializers.ModelSerializer):
    event_system_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = LogsPattern
        fields = ['pattern', 'event_system_id']

    def create(self, validated_data):
        # Extract the event system ID and pattern from the validated data
        event_system_id = validated_data.pop('event_system_id')
        pattern = validated_data.get('pattern')

        try:
            # Fetch the EventSystemConfiguration related to the event system ID
            event_system = EventSystem.objects.get(id=event_system_id)
            config = EventSystemConfiguration.objects.get(event_system=event_system)

            # Create a new log pattern
            log_pattern = LogsPattern.objects.create(pattern=pattern)

            # Link the log pattern to the event system configuration
            config.logs_pattern = log_pattern
            config.save()

            return log_pattern

        except EventSystem.DoesNotExist:
            raise serializers.ValidationError("Event system not found")
        except EventSystemConfiguration.DoesNotExist:
            raise serializers.ValidationError("Event system configuration not found")
        except Exception as e:
            raise serializers.ValidationError(str(e))
