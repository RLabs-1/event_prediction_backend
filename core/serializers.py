from rest_framework import serializers
from core.models import EventSystem


class EventSystemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSystem
        fields = ['name']