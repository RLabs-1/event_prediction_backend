from django.shortcuts import render

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from user_management.services.services import EventSystemFileService

class EventSystemFileView(APIView):
    def delete(self, request, eventSystemId, fileId):
        EventSystemFileService.delete_file(eventSystemId, fileId)
        return Response({"message": "File deleted successfully"}, status=status.HTTP_204_NO_CONTENT)