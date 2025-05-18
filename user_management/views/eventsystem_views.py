#from rest_framework.views import APIView
#from rest_framework.response import Response
#from rest_framework import status
#from core.models import EventSystem, EventSystemConfiguration
#from user_management.serializers.eventsystem_serializers import EventSystemConfigurationSerializer
#from django.shortcuts import get_object_or_404
#from rest_framework.permissions import IsAuthenticated

#class PatchEventSystemConfigurationView(APIView):
#    permission_classes = [IsAuthenticated]  # optional

#    def patch(self, request, id):
#        event_system = get_object_or_404(EventSystem, id=id)
#        config = get_object_or_404(EventSystemConfiguration, event_system=event_system)

#        serializer = EventSystemConfigurationSerializer(config, data=request.data, partial=True)
#        if serializer.is_valid():
#            serializer.save()
#            return Response(serializer.data)
#        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# user_management/views/eventsystem_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from core.models import EventSystem
from user_management.serializers.eventsystem_serializers import EventSystemConfigurationSerializer


class EventSystemConfigurationPatchView(APIView):
    def patch(self, request, id):
        # Fetch the EventSystem object by UUID
        event_system = get_object_or_404(EventSystem, id=id)

        # Pass partial=True to allow partial updates
        serializer = EventSystemConfigurationSerializer(event_system, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
