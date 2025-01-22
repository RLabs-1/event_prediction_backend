from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import FileReference
from file_manager.serializers.serializers import FileReferenceSerializer

class FileReferenceUpdateFileNameView(UpdateAPIView):
    queryset = FileReference.objects.all()
    serializer_class = FileReferenceSerializer
    lookup_field = 'id'  # The field to use for lookup
    lookup_url_kwarg = 'fileId'  # The URL keyword argument for fileId
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def partial_update(self, request, *args, **kwargs):
        # Access eventSystemId from the URL (if needed)
        event_system_id = kwargs.get('eventSystemId')
        # Access fileId from the URL
        file_id = kwargs.get('fileId')
        # Get the FileReference object
        instance = self.get_object()
        # Validate and update the file_name
        new_file_name = request.data.get('file_name')
        if not new_file_name or len(new_file_name.strip()) == 0:
            return Response({"error": "file_name is required and cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

        instance.file_name = new_file_name
        instance.save()

        # Serialize and return the updated data
        serializer = self.get_serializer(instance)
        return Response(serializer.data)