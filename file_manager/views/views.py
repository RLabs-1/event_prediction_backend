from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from file_manager.services.services import deselect_file, EventSystemService, EventSystemFileService, FileService
from django.conf import settings
from core.models import EventSystem
from file_manager.serializers.serializers import EventSystemNameUpdateSerializer, EventSystemSerializer
from django.shortcuts import get_object_or_404
import os
from core.models import EventSystem
from file_manager.serializers.serializers import FileReferenceSerializer

from rest_framework.generics import CreateAPIView
from core.models import EventSystem, EventStatus
from file_manager.serializers.serializers import EventSystemCreateSerializer, FileReferenceSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import APIException, ValidationError, NotFound
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler


class EventSystemCreateView(CreateAPIView):
    """View to create an EventSystem"""
    queryset = EventSystem.objects.all()
    serializer_class = EventSystemCreateSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        """Use the EventSystemService to handle the creation logic."""
        try:
            name = serializer.validated_data['name']
            EventSystemService.create_event_system(name=name, user=self.request.user)
        except ValidationError as e:
            # Raise validation errors to match serializer errors
            raise ValidationError({'error': str(e)})
        except Exception as e:
            # Catch all unexpected errors and log them
            raise APIException({'error': 'An unexpected error occurred. Please try again later.'+ str(e)})

    def create(self, request, *args, **kwargs):
        """Override the create method to handle response format for errors."""
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except APIException as e:
            return Response({'error': e.detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # For unexpected exceptions
            return Response(
                {'error': 'Something went wrong. Please contact support.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ActivateEventSystemView(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request, eventSystemId):
        """Activate an EventSystem."""
        try:
            # Attempt to update the status of the EventSystem
            event_system = EventSystemService.update_status(eventSystemId, EventStatus.ACTIVE, request.user)
            return Response({
                "message": "EventSystem activated successfully.",
                "eventSystemId": str(event_system.uuid),
                "status": event_system.status,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            # Handle invalid values or data
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except EventSystem.DoesNotExist:
            # Handle cases where the EventSystem ID does not exist
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)

        except PermissionDenied:
            # Handle permission-related errors
            return Response({"error": "You do not have permission to activate this EventSystem."},
                            status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            # Catch all unexpected errors
            return Response(
                {"error": "An unexpected error occurred. Please try again later."+str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DeactivateEventSystemView(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request, eventSystemId):
        """Deactivate an EventSystem."""
        try:
            # Attempt to update the status of the EventSystem
            event_system = EventSystemService.update_status(eventSystemId, EventStatus.INACTIVE, request.user)
            return Response({
                "message": "EventSystem deactivated successfully.",
                "eventSystemId": str(event_system.uuid),
                "status": event_system.status,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            # Handle invalid values or data
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except EventSystem.DoesNotExist:
            # Handle cases where the EventSystem ID does not exist
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)

        except PermissionDenied:
            # Handle permission-related errors
            return Response({"error": "You do not have permission to deactivate this EventSystem."},
                            status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            # Catch all unexpected errors
            return Response(
                {"error": "An unexpected error occurred. Please try again later."+ str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EventSystemFileView(APIView):
    def delete(self, request, eventSystemId, fileId):
        """Delete a file associated with an EventSystem."""
        try:
            # Attempt to delete the file using the service
            EventSystemFileService.delete_file(eventSystemId, fileId)
            return Response({"message": "File deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

        except EventSystemFileService.FileNotFoundError:
            # Handle case where the file or EventSystem doesn't exist
            return Response({"error": "File or EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)

        except PermissionDenied:
            # Handle permission-related errors
            return Response({"error": "You do not have permission to delete this file."},
                            status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            # Catch any other unexpected errors
            return Response(
                {"error": "An unexpected error occurred. Please try again later."+str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class DeselectFileView(APIView):
    """
    View to handle the deselecting of a file in an EventSystem.
    """

    def patch(self, request, eventSystemId, fileId):
        try:
            # Call the service or function to deselect the file
            response = deselect_file(eventSystemId, fileId)
            return Response(response, status=status.HTTP_200_OK)

        except ValueError as e:
            # Handle invalid arguments or business logic errors
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except FileNotFoundError:
            # Handle cases where the file or EventSystem doesn't exist
            return Response({"error": "File or EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)

        except PermissionDenied:
            # Handle permission-related errors
            return Response({"error": "You do not have permission to deselect this file."},
                            status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            # Catch all unexpected errors
            return Response(
                {"error": "An unexpected error occurred. Please try again later."+str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, eventSystemId):
        try:
            # Check if a file is provided in the request
            file = request.FILES.get('file')
            if not file:
                raise ValidationError("No file provided.")

            # Extract file details
            filename = file.name
            file_path = os.path.join(settings.MEDIA_ROOT, filename)

            # Save the file to the media directory
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            # Generate file URL for the response
            file_url = settings.MEDIA_URL + filename
            return Response(
                {'message': 'File uploaded successfully', 'file_url': file_url},
                status=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            # Handle validation errors
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError:
            # Handle permission errors when saving the file
            return Response(
                {'error': 'Permission denied while saving the file. Check server permissions.'},
                status=status.HTTP_403_FORBIDDEN
            )

        except FileExistsError:
            # Handle cases where a file with the same name already exists
            return Response(
                {'error': 'A file with the same name already exists. Please use a unique filename.'},
                status=status.HTTP_409_CONFLICT
            )

        except Exception as e:
            # Handle all unexpected errors
            return Response(
                {'error': 'An unexpected error occurred during file upload. Please try again later.'+str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EventSystemNameUpdateView(APIView):
    """
    Handles updating the name of an EventSystem via PATCH request.
    """
    def patch(self, request, eventSystemId):
        try:
            # Retrieve the EventSystem object by its UUID
            event_system = get_object_or_404(EventSystem, uuid=eventSystemId)

            # Initialize serializer with partial update
            serializer = EventSystemNameUpdateSerializer(event_system, data=request.data, partial=True)

            if serializer.is_valid():
                # Save the updated name
                serializer.save()
                return Response(
                    {"message": "EventSystem name updated successfully."},
                    status=status.HTTP_200_OK
                )
            else:
                # Return validation errors from the serializer
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            # Handle validation-related errors
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except EventSystem.DoesNotExist:
            # Handle case when EventSystem is not found
            return Response(
                {"error": f"EventSystem with ID '{eventSystemId}' does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            # Catch-all for unexpected errors
            return Response(
                {"error": "An unexpected error occurred while updating the EventSystem name."+str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FileRetrieveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, eventSystemId, fileId):
        try:
            # Attempt to retrieve the file via FileService
            file = FileService.get_file(eventSystemId, fileId, request.user)

            # Serialize and return the file data
            return Response(FileReferenceSerializer(file).data)

        except PermissionDenied as e:
            # Handle permission denied error (e.g., user not authorized)
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
          
        except NotFound as e:
            # Handle case where the file or event system is not found
            return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            # Handle invalid parameter errors (e.g., invalid fileId or eventSystemId)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Catch-all for any unexpected errors
            return Response(
                {"error": "An unexpected error occurred while retrieving the file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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


