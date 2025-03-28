from rest_framework import serializers
from core.models import EventSystem, FileReference

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


