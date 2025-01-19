from rest_framework import serializers
from core.models import EventSystem,User

class EventSystemSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all()
    )
    class Meta:
        model = EventSystem
        fields = '__all__'
