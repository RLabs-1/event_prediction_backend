from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from file_manager.services.services import deselect_file, EventSystemService, EventSystemFileService, FileService
from file_manager.serializers.serializers import EventSystemNameUpdateSerializer, EventSystemCreateSerializer
from django.conf import settings
from core.models import EventSystem, FileReference
from file_manager.serializers.serializers import EventSystemNameUpdateSerializer, EventSystemSerializer, FileReferenceSerializer
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from core.models import EventSystem, EventStatus
import os

from rest_framework.generics import CreateAPIView
from core.models import EventSystem, EventStatus
from file_manager.serializers.serializers import EventSystemCreateSerializer, FileReferenceSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
import aiofiles

from core.models import EventSystem
from file_manager.serializers.serializers import EventSystemNameUpdateSerializer, EventSystemSerializer

from file_manager.serializers.serializers import FileReferenceSerializer
from file_manager.serializers.serializers import EventSystemCreateSerializer, FileReferenceSerializer
from rest_framework import viewsets
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import APIException, ValidationError, NotFound
from rest_framework.views import exception_handler
from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiTypes
from django.http import FileResponse


class EventSystemCreateView(APIView):
    """View to create an EventSystem"""
    permission_classes = [IsAuthenticated]  # Requires authentication
    
    @extend_schema(
        tags=['file manager'],
        description='Create a new event system. User must be authenticated.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': 'Name of the event system'},
                },
                'required': ['name']
            }
        },
        responses={
            201: {
                'description': 'Event system created successfully',
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'name': {'type': 'string'},
                    'message': {'type': 'string'}
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
        },
        examples=[
            OpenApiExample(
                'Create Example',
                value={
                    'name': 'My Event System'
                },
                request_only=True
            )
        ]
    )
    def post(self, request):
        """Create a new event system for the authenticated user."""
        try:
            name = request.data.get('name')
            if not name:
                return Response(
                    {"error": "Name is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create event system and associate with user
            event_system = EventSystem.objects.create(name=name)
            event_system.users.add(request.user)

            return Response({
                'id': event_system.uuid,
                'name': event_system.name,
                'message': 'Event system created successfully'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ActivateEventSystemView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=['file manager'],
        description='Activate an EventSystem.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'eventSystemId': {'type': 'string', 'format': 'uuid', 'description': 'ID of the event system'},
                },
                'required': ['eventSystemId']
            }
        },
        responses={
            200: {
                'description': 'EventSystem activated successfully.',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'eventSystemId': {'type': 'string', 'format': 'uuid'},
                    'status': {'type': 'string'}
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            404: {'description': 'EventSystem not found'},
            403: {'description': 'Permission denied'},
            500: {'description': 'An unexpected error occurred. Please try again later.'}
        },
        examples=[
            OpenApiExample(
                'Activate Example',
                value={
                    'eventSystemId': '00000000-0000-0000-0000-000000000000'
                },
                request_only=True
            )
        ]
    )
    def patch(self, request, eventSystemId):
        """Activate an EventSystem."""
        try:
            # Attempt to update the status of the EventSystem
            event_system = EventSystemService.update_status(eventSystemId, EventStatus.ACTIVE, request.user)
            return Response({
                "message": "EventSystem activated successfully.",
                "eventSystemId": str(event_system.id),
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

    @extend_schema(
        tags=['file manager'],
        description='Deactivate an EventSystem.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'eventSystemId': {'type': 'string', 'format': 'uuid', 'description': 'ID of the event system'},
                },
                'required': ['eventSystemId']
            }
        },
        responses={
            200: {
                'description': 'EventSystem deactivated successfully.',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'eventSystemId': {'type': 'string', 'format': 'uuid'},
                    'status': {'type': 'string'}
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            404: {'description': 'EventSystem not found'},
            403: {'description': 'Permission denied'},
            500: {'description': 'An unexpected error occurred. Please try again later.'}
        },
        examples=[
            OpenApiExample(
                'Deactivate Example',
                value={
                    'eventSystemId': '00000000-0000-0000-0000-000000000000'
                },
                request_only=True
            )
        ]
    )
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

    @extend_schema(
        tags=['file manager'],
        description='Deselect a file in event system',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'eventSystemId': {'type': 'string', 'format': 'uuid', 'description': 'ID of the event system'},
                    'fileId': {'type': 'string', 'format': 'uuid', 'description': 'ID of the file to deselect'}
                },
                'required': ['eventSystemId', 'fileId']
            }
        },
        responses={
            200: {
                'description': 'File deselected successfully',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'fileId': {'type': 'string', 'format': 'uuid'},
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'File or event system not found'},
        }
    )
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

    @extend_schema(
        tags=['file manager'],
        description='Upload a file to event system',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'},
                },
                'required': ['file']
            }
        },
        responses={
            201: {
                'description': 'File uploaded successfully',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'file_url': {'type': 'string'},
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            409: {'description': 'Conflict'},
        }
    )
    async def post(self, request):
        try:
            file = request.FILES.get('file')
            if not file:
                return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

            # Extract file details
            filename = file.name
            file_path = os.path.join(settings.MEDIA_ROOT, filename)

            # Use aiofiles to handle file operations asynchronously
            async with aiofiles.open(file_path, 'wb+') as destination:
                # Iterate through the file chunks and write asynchronously
                for chunk in file.chunks():
                    await destination.write(chunk)

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
    @extend_schema(
        tags=['file manager'],
        description='Update event system name',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': 'New name of the event system'},
                },
                'required': ['name']
            }
        },
        responses={
            200: {
                'description': 'EventSystem name updated successfully',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            404: {'description': 'EventSystem not found'},
        }
    )
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

    @extend_schema(
        tags=['file manager'],
        description='Retrieve a file from event system',
        parameters=[
            OpenApiParameter(
                name='eventSystemId',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='ID of the event system'
            ),
            OpenApiParameter(
                name='fileId',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='ID of the file to retrieve'
            )
        ],
        responses={
            200: {'description': 'File retrieved successfully'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'File or event system not found'},
        }
    )
    def get(self, request, eventSystemId, fileId):
        try:
            # Get the event system
            event_system = EventSystem.objects.get(id=eventSystemId)
            
            # Check if user has access to this event system
            if event_system.owner != request.user and not request.user.is_superuser:
                return Response(
                    {"error": "You don't have permission to access this file"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get the file
            file_reference = FileReference.objects.get(
                id=fileId,
                event_system=event_system
            )
            
            # Return the file
            response = FileResponse(file_reference.file)
            response['Content-Disposition'] = f'attachment; filename="{file_reference.file_name}"'
            return response
            
        except EventSystem.DoesNotExist:
            return Response(
                {"error": "Event system not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except FileReference.DoesNotExist:
            return Response(
                {"error": "File not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FileReferenceUpdateFileNameView(UpdateAPIView):
    queryset = FileReference.objects.all()
    serializer_class = FileReferenceSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'fileId'
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['file manager'],
        description='Update file name in event system (PUT)',
        parameters=[
            OpenApiParameter(
                name='eventSystemId',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of the event system'
            ),
            OpenApiParameter(
                name='fileId',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of the file'
            )
        ],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'file_name': {'type': 'string', 'description': 'New name of the file'}
                },
                'required': ['file_name']
            }
        },
        responses={
            200: FileReferenceSerializer,
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            404: {'description': 'File not found'}
        }
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @extend_schema(
        tags=['file manager'],
        description='Partially update file name in event system (PATCH)',
        parameters=[
            OpenApiParameter(
                name='eventSystemId',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of the event system'
            ),
            OpenApiParameter(
                name='fileId',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of the file'
            )
        ],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'file_name': {'type': 'string', 'description': 'New name of the file'}
                }
            }
        },
        responses={
            200: FileReferenceSerializer,
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            404: {'description': 'File not found'}
        }
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

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


class FileSelectView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['file manager'],
        description='Select a file in event system',
        parameters=[
            OpenApiParameter(
                name='eventSystemId',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='ID of the event system'
            ),
            OpenApiParameter(
                name='fileId',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='ID of the file to select'
            )
        ],
        responses={
            200: {
                'description': 'File selected successfully',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'fileId': {'type': 'string', 'format': 'uuid'},
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'File or event system not found'},
        }
    )
    def post(self, request, eventSystemId, fileId):
        try:
            # Get the event system
            event_system = EventSystem.objects.get(id=eventSystemId)
            
            # Check if user has access to this event system
            if event_system.owner != request.user and not request.user.is_superuser:
                return Response(
                    {"error": "You don't have permission to access this event system"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get the file
            file_reference = FileReference.objects.get(
                id=fileId,
                event_system=event_system
            )
            
            # Update file status to selected
            file_reference.is_selected = True
            file_reference.save()
            
            return Response({
                'message': 'File selected successfully',
                'fileId': str(file_reference.id)
            }, status=status.HTTP_200_OK)
            
        except EventSystem.DoesNotExist:
            return Response(
                {"error": "Event system not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except FileReference.DoesNotExist:
            return Response(
                {"error": "File not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

