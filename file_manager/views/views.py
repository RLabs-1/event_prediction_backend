from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from file_manager.services.services import deselect_file
from django.conf import settings
from core.models import EventSystem
from file_manager.serializers.serializers import EventSystemNameUpdateSerializer
from django.shortcuts import get_object_or_404
import os

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