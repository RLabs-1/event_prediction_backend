from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from core.models import EventSystem
from user_management.serializers.eventsystem_serializers import EventSystemConfigurationSerializer
from drf_spectacular.utils import extend_schema

class EventSystemConfigurationPatchView(APIView):

    @extend_schema(
        request=EventSystemConfigurationSerializer,
        responses=EventSystemConfigurationSerializer,
        methods=['PATCH'],
        description="Partially update EventSystem configuration"
    )

    def patch(self, request, id):
        # Fetch the EventSystem object by UUID
        event_system = get_object_or_404(EventSystem, id=id)

        # Pass partial=True to allow partial updates
        serializer = EventSystemConfigurationSerializer(event_system, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
