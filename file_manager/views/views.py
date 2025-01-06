from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from file_manager.services.services import deselect_file


class DeselectFileView(APIView):
    """
       View to handle the deselecting of a file in an EventSystem.
    """
    def patch(self, request, eventSystemId, fileId):
        response = deselect_file(eventSystemId, fileId)
        return Response(response, status=status.HTTP_200_OK)