from rest_framework import viewsets
from core.models import EventSystem
from file_manager.serializers.serializers import EventSystemSerializer

class EventSystemViewSet(viewsets.ModelViewSet):
    queryset = EventSystem.objects.all()
    serializer_class = EventSystemSerializer