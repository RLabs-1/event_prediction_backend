from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from file_manager.services.services import deselect_file, EventSystemService, EventSystemFileService, FileService
from django.conf import settings
from core.models import EventSystem
from file_manager.serializers.serializers import EventSystemNameUpdateSerializer
from django.shortcuts import get_object_or_404
import os
from rest_framework.generics import CreateAPIView
from core.models import EventSystem, EventStatus
from file_manager.serializers.serializers import EventSystemCreateSerializer, FileSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from django.core.exceptions import PermissionDenied



class EventSystemCreateView(CreateAPIView):
    """View to create an EventSystem """
    queryset = EventSystem.objects.all()
    serializer_class = EventSystemCreateSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        """Use the EventSystemService to handle the creation logic."""
        name = serializer.validated_data['name']
        EventSystemService.create_event_system(name=name, user=self.request.user)


class ActivateEventSystemView(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request, eventSystemId):
        """Activate an EventSystem."""
        try:
            event_system = EventSystemService.update_status(eventSystemId, EventStatus.ACTIVE, request.user)
            return Response({
                "message": "EventSystem activated successfully.",
                "eventSystemId": str(event_system.uuid),
                "status": event_system.status,
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeactivateEventSystemView(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request, eventSystemId):
        """Deactivate an EventSystem."""
        try:
            event_system = EventSystemService.update_status(eventSystemId, EventStatus.INACTIVE, request.user)
            return Response({
                "message": "EventSystem deactivated successfully.",
                "eventSystemId": str(event_system.uuid),
                "status": event_system.status,
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EventSystemFileView(APIView):
    def delete(self, request, eventSystemId, fileId):
        EventSystemFileService.delete_file(eventSystemId, fileId)
        return Response({"message": "File deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

class DeselectFileView(APIView):
    """
       View to handle the deselecting of a file in an EventSystem.
    """
    def patch(self, request, eventSystemId, fileId):
        response = deselect_file(eventSystemId, fileId)
        return Response(response, status=status.HTTP_200_OK)

class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, eventSystemId):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        filename = file.name
        file_path = os.path.join(settings.MEDIA_ROOT, filename)

        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        file_url = settings.MEDIA_URL + filename
        return Response({'message': 'File uploaded successfully', 'file_url': file_url}, status=status.HTTP_201_CREATED)
      
class EventSystemNameUpdateView(APIView):
    """
    Handles updating the name of an EventSystem via PATCH request.
    """
    def patch(self, request, eventSystemId):
        event_system = get_object_or_404(EventSystem, uuid=eventSystemId)
        serializer = EventSystemNameUpdateSerializer(event_system, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "EventSystem name updated successfully."}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FileRetrieveView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, eventSystemId, fileId):
        try:
            file = FileService.get_file(eventSystemId, fileId, request.user)
            return Response(FileSerializer(file).data)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

