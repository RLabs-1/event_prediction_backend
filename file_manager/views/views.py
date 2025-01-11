from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from file_manager.services.services import deselect_file
from django.conf import settings
import os
from core.models import EventSystem
from file_manager.serializers.serializers import FileReferenceSerializer

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



class EventSystemFileListView(APIView):
    """
    This view retrieves all files associated with a specific EventSystem.
    """
    def get(self, request, eventSystemId):
        try:
            event_system = EventSystem.objects.get(uuid=eventSystemId)
            files = event_system.file_objects.all()
            if not files:
                return Response(
                    {"message": "No files associated with this EventSystem", "files": []},
                    status=status.HTTP_200_OK
                )
            serializer = FileReferenceSerializer(files, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except EventSystem.DoesNotExist:
            return Response({"detail": "EventSystem not found"}, status=status.HTTP_404_NOT_FOUND)