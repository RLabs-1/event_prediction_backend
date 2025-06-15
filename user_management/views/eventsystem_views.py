from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.models import EventSystemConfiguration
from user_management.serializers.eventsystem_serializers import EventSystemConfigurationPatchSerializer


class EventSystemConfigurationPatchView(APIView):
    serializer_class = EventSystemConfigurationPatchSerializer
    
    def patch(self, request, eventSystemId, configurationId):
        config = EventSystemConfiguration.objects.filter(
            id=configurationId,
            event_system_id=eventSystemId
        ).first()

        if not config:
            return Response(
                {"message": "Configuration not found for the given Event System."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EventSystemConfigurationPatchSerializer(
            config, data=request.data, partial=True
        )

        if serializer.is_valid(): #if valid save it
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
