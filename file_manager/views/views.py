from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from file_manager.services.services import deselect_file, EventSystemService
from django.conf import settings
import os
from rest_framework.permissions import IsAuthenticated
from core.models import EventStatus

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

class DeselectFileView(APIView):
    """
       View to handle the deselecting of a file in an EventSystem.
    """
    def patch(self, request, eventSystemId, fileId):
        response = deselect_file(eventSystemId, fileId)
        return Response(response, status=status.HTTP_200_OK)

# Handle file uploads
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