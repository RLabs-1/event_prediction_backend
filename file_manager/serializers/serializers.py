from rest_framework import serializers
from core.models import FileReference, EventSystem


class FileReferenceSerializer(serializers.ModelSerializer)
    class Meta:
        model = FileReference
        fields = '__all__'


class EventSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSystem
        fields = '__all__'