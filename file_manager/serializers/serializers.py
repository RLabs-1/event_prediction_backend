from rest_framework import serializers
from core.models import FileReference, EventSystem



class EventSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSystem
        fields = '__all__'