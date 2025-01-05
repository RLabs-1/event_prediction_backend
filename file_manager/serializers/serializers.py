from rest_framework import serializers
from core.models import FileReference

class FileReferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for the FileReference model.
    Handles serialization and deserialization of FileReference instances.
    """
    class Meta:
        model = FileReference
        fields = '__all__'  # Include all fields or specify them explicitly
