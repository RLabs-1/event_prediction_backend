from rest_framework import serializers
from core.models import EventSystem, FileReference

class EventSystemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSystem
        fields = ['name']

class FileReferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for the FileReference model.
    Handles serialization and deserialization of FileReference instances.
    """
    class Meta:
        model = FileReference
        fields = '__all__'  # Include all fields or specify them explicitly

class EventSystemSerializer(serializers.ModelSerializer):
    """
        Serializer for the EventSystem model.
    """
    class Meta:
        model = EventSystem # Include all fields or specify them explicitly
        fields = '__all__'

class EventSystemNameUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSystem
        fields = ['name']  # Only allow updating the name field        

