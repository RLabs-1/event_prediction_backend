from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
import os
from rest_framework.permissions import IsAuthenticated

from core.models import EventSystem, EventStatus, FileReference
from file_manager.services.services import EventSystemService, EventSystemFileService
from file_manager.serializers.serializers import EventSystemNameUpdateSerializer, FileReferenceSerializer, EventSystemCreateSerializer

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter, OpenApiTypes
from django.http import FileResponse

from loguru import logger


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
            # Log the incoming request
            logger.info(
                f"Received request to create event system: "
                f"user_id={request.user.id}, data={request.data}"
            )

            # Validate the request data
            serializer = EventSystemCreateSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(
                    f"Event system creation failed: Validation errors: {serializer.errors}"
                )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Create the event system
            event_system = EventSystemService.create_event_system(
                serializer.validated_data['name'], request.user
            )
            logger.info(
                f"Event system created successfully: "
                f"event_system_id={event_system.id}, user_id={request.user.id}"
            )

            # Return the response
            return Response(
                EventSystemCreateSerializer(event_system).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Error creating event system for user_id={request.user.id}: {e}"
            )
            return Response(
                {"error": "Something went wrong while creating the event system."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class EventSystemNameUpdateView(APIView):
    """
    Handles updating the name of an EventSystem via PATCH request.
    """
    permission_classes = [IsAuthenticated]

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
            403: {'description': 'Permission denied - You do not have permission to update this EventSystem.'},
            404: {'description': 'EventSystem not found'},
            500: {'description': 'An unexpected error occurred. Please try again later.'}
        }
    )
    def patch(self, request, eventSystemId):
        try:
            # Log the incoming request
            logger.info(
                f"Received request to update event system name: "
                f"user_id={request.user.id}, event_system_id={eventSystemId}, data={request.data}"
            )

            # Get the event system
            event_system = EventSystem.objects.get(uuid=eventSystemId)
            logger.debug(f"Event system found: event_system_id={eventSystemId}")

            # Check if the user is authorized to update this EventSystem
            if request.user not in event_system.users.all():
                logger.warning(
                    f"Event system name update failed: Permission denied. "
                    f"User ID ({request.user.id}) is not authorized to update event system ID ({eventSystemId})"
                )
                raise PermissionError("Permission denied – You do not have permission to update this EventSystem.")

            # Use serializer for validation
            serializer = EventSystemNameUpdateSerializer(event_system, data=request.data, partial=True)

            if not serializer.is_valid():
                logger.warning(
                    f"Event system name update failed: Validation errors: {serializer.errors}"
                )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Ensure 'name' exists in validated data
            if 'name' not in serializer.validated_data:
                logger.warning(
                    f"Event system name update failed: 'name' field is required. "
                    f"Request data: {request.data}"
                )
                raise ValueError("Invalid request. 'name' field is required.")

            # Update the event system name
            updated_event_system = EventSystemService.update_event_system_name(event_system, serializer.validated_data['name'])
            logger.info(
                f"Event system name updated successfully: "
                f"event_system_id={eventSystemId}, new_name={serializer.validated_data['name']}"
            )

            return Response({"message": "EventSystem name updated successfully."}, status=status.HTTP_200_OK)

        except EventSystem.DoesNotExist:
            logger.warning(f"Event system name update failed: Event system not found for event_system_id={eventSystemId}")
            return Response({"error": "Event system not found"}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            logger.warning(f"Event system name update failed: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError as e:
            logger.warning(f"Event system name update failed: {e}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            logger.error(
                f"Error updating event system name for event_system_id={eventSystemId}: {e}"
            )
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ActivateEventSystemView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=['file manager'],
        description='Activate an EventSystem.',
        request=None,
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
            403: {'description': 'Permission denied - You do not have permission to activate this EventSystem.'},
            404: {'description': 'EventSystem not found'},
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
            # Log the incoming request
            logger.info(
                f"Received request to activate event system: "
                f"user_id={request.user.id}, event_system_id={eventSystemId}"
            )

            # Attempt to update the status of the EventSystem
            event_system = EventSystemService.update_status(eventSystemId, EventStatus.ACTIVE, request.user)
            logger.info(
                f"Event system activated successfully: "
                f"event_system_id={eventSystemId}, status={event_system.status}"
            )

            return Response({
                "message": "EventSystem activated successfully.",
                "eventSystemId": str(event_system.id),
                "status": event_system.status,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            # Handle invalid values or data
            logger.warning(f"Event system activation failed: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except EventSystem.DoesNotExist:
            # Handle cases where the EventSystem ID does not exist
            logger.warning(f"Event system activation failed: Event system not found for event_system_id={eventSystemId}")
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)

        except PermissionError:
            # Handle permission-related errors
            logger.warning(
                f"Event system activation failed: Permission denied. "
                f"User ID ({request.user.id}) is not authorized to activate event system ID ({eventSystemId})"
            )
            return Response({"error": "You do not have permission to activate this EventSystem."},
                            status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            # Catch all unexpected errors
            logger.error(
                f"Error activating event system for event_system_id={eventSystemId}: {e}"
            )
            return Response(
                {"error": "An unexpected error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeactivateEventSystemView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=['file manager'],
        description='Deactivate an EventSystem.',
        request=None,
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
            403: {'description': 'Permission denied - You do not have permission to deactivate this EventSystem.'},
            404: {'description': 'EventSystem not found'},
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
            # Log the incoming request
            logger.info(
                f"Received request to deactivate event system: "
                f"user_id={request.user.id}, event_system_id={eventSystemId}"
            )

            # Attempt to update the status of the EventSystem
            event_system = EventSystemService.update_status(eventSystemId, EventStatus.INACTIVE, request.user)
            logger.info(
                f"Event system deactivated successfully: "
                f"event_system_id={eventSystemId}, status={event_system.status}"
            )

            return Response({
                "message": "EventSystem deactivated successfully.",
                "eventSystemId": str(event_system.uuid),
                "status": event_system.status,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            # Handle invalid values or data
            logger.warning(f"Event system deactivation failed: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except EventSystem.DoesNotExist:
            # Handle cases where the EventSystem ID does not exist
            logger.warning(f"Event system deactivation failed: Event system not found for event_system_id={eventSystemId}")
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)

        except PermissionError as e:
            # Handle permission-related errors
            logger.warning(
                f"Event system deactivation failed: Permission denied. "
                f"User ID ({request.user.id}) is not authorized to deactivate event system ID ({eventSystemId})"
            )
            return Response({"error": "You do not have permission to deactivate this EventSystem."},
                            status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            # Catch all unexpected errors
            logger.error(
                f"Error deactivating event system for event_system_id={eventSystemId}: {e}"
            )
            return Response(
                {"error": "An unexpected error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from loguru import logger

class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAuthenticated,)

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
            201: {'description': 'File uploaded successfully'},
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'EventSystem not found'},
            409: {'description': 'Conflict'},
        }
    )
    def post(self, request, eventSystemId):
        """Upload file to event system"""
        file = request.FILES.get('file')

        # Log request details
        logger.info(
            f"Received file upload request: user_id={request.user.id}, "
            f"event_system_id={eventSystemId}, file_name={file.name if file else 'No file provided'}"
        )

        if not file:
            logger.warning(f"File upload failed: No file provided by user_id={request.user.id}")
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Upload the file
            file_reference = EventSystemFileService.upload_file(file, eventSystemId, request.user)

            # Log successful upload
            logger.info(
                f"File uploaded successfully: user_id={request.user.id}, "
                f"event_system_id={eventSystemId}, file_id={file_reference.id}, file_url={file_reference.url}"
            )

            return Response({
                "message": "File uploaded successfully",
                "file_url": file_reference.url,
                "file_id": file_reference.id
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            logger.warning(f"File upload failed (ValueError): {e} (user_id={request.user.id}, event_system_id={eventSystemId})")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except EventSystem.DoesNotExist:
            logger.warning(f"File upload failed: EventSystem not found (event_system_id={eventSystemId})")
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)

        except PermissionError as e:
            logger.warning(f"File upload failed (PermissionError): {e} (user_id={request.user.id}, event_system_id={eventSystemId})")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except FileExistsError:
            logger.warning(
                f"File upload failed (FileExistsError): Duplicate file name (user_id={request.user.id}, "
                f"event_system_id={eventSystemId}, file_name={file.name})"
            )
            return Response(
                {'error': 'A file with the same name already exists. Please use a unique filename.'},
                status=status.HTTP_409_CONFLICT
            )

        except Exception as e:
            logger.error(f"Unexpected error during file upload: {e} (user_id={request.user.id}, event_system_id={eventSystemId})")
            return Response(
                {"error": "An unexpected error occurred while uploading the file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FileReferenceView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=['file manager'],
        description='Deleting a file',
        responses={
            200: {
                'description': 'File deleted successfully',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'file_id': {'type': 'string'},
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'File or EventSystem not found'},
        }
    )
    def delete(self, request, eventSystemId, fileId):
        """Delete file from event system"""
        try:
            logger.info(f"User {request.user} attempting to delete file {fileId} from event system {eventSystemId}.")
            file_id = EventSystemFileService.delete_file(eventSystemId, fileId, request.user)
            logger.info(f"File {file_id} deleted successfully.")
            return Response({
                "message": "File deleted successfully",
                "file_id": str(file_id)
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning(f"Bad request: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except EventSystem.DoesNotExist:
            logger.error("EventSystem not found.")
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)

        except FileReference.DoesNotExist:
            logger.error("FileReference not found.")
            return Response({"error": "FileReference not found."}, status=status.HTTP_404_NOT_FOUND)

        except PermissionError as e:
            logger.warning(f"Permission denied: {e}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            logger.exception("Unexpected error occurred.")
            return Response(
                {"error": "An unexpected error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
            400: {'description': 'File does not belong to the EventSystem'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'File or event system not found'},
        }
    )
    def get(self, request, eventSystemId, fileId):
        """Retrieve a file from event system"""
        try:
            logger.info(f"User {request.user} retrieving file {fileId} from event system {eventSystemId}.")
            event_system = EventSystem.objects.get(uuid=eventSystemId)
            file_reference = FileReference.objects.get(id=fileId)

            if (request.user not in event_system.users.all()) and (not request.user.is_superuser):
                raise PermissionError("You do not have access to this file.")

            if not event_system.file_objects.filter(id=fileId).exists():
                raise ValueError("File does not belong to this EventSystem.")

            relative_path = file_reference.url.replace(settings.MEDIA_URL, "").lstrip("/")
            file_path = os.path.join(settings.MEDIA_ROOT, relative_path)

            if not os.path.exists(file_path):
                raise ValueError(f"File not found at: {file_path}")

            logger.info(f"File {fileId} found and being returned.")
            return FileResponse(open(file_path, 'rb'), content_type='application/octet-stream', as_attachment=True)

        except EventSystem.DoesNotExist:
            logger.error("Event system not found.")
            return Response({"error": "Event system not found"}, status=status.HTTP_404_NOT_FOUND)

        except FileReference.DoesNotExist:
            logger.error("File not found.")
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            logger.warning(f"Bad request: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError as e:
            logger.warning(f"Permission denied: {e}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            logger.exception("Unexpected error occurred.")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        tags=['file manager'],
        description='Update file name in event system (patch)',
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
            200: {
                'description': 'File name updated successfully',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'new_file_name': {'type': 'string'},
                    'file_id': {'type': 'string'},
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'File or EventSystem not found'},
            409: {'description': 'Conflict'},
        }
    )
    def patch(self, request, eventSystemId, fileId):
        """Patch file name in the event system"""
        new_file_name = request.data.get('file_name')
        try:
            if not new_file_name:
                raise ValueError("File name is required.")

            logger.info(f"User {request.user} updating file {fileId} name to {new_file_name} in event system {eventSystemId}.")
            updated_file = EventSystemFileService.update_file_name(eventSystemId, fileId, new_file_name, request.user)
            logger.info(f"File {fileId} name updated successfully.")
            return Response({
                "message": "File name updated successfully",
                "new_file_name": new_file_name,
                "file_id": str(fileId)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception("Unexpected error occurred.")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    def patch(self, request, eventSystemId, fileId):
        """Flag a file as selected"""
        user_id = request.user.id
        logger.info(f"User {user_id} requested to select file {fileId} in event system {eventSystemId}")

        try:
            file_reference = EventSystemFileService.flag_file(eventSystemId, fileId, request.user, action='select')

            logger.info(f"File {fileId} successfully selected in event system {eventSystemId} by user {user_id}")
            return Response({
                'message': 'File selected successfully',
                'fileId': str(file_reference.id)
            }, status=status.HTTP_200_OK)

        except EventSystem.DoesNotExist:
            logger.warning(f"Event system {eventSystemId} not found (User {user_id})")
            return Response({"error": "Event system not found"}, status=status.HTTP_404_NOT_FOUND)

        except FileReference.DoesNotExist:
            logger.warning(f"File {fileId} not found in event system {eventSystemId} (User {user_id})")
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            logger.warning(f"Invalid request for selecting file {fileId} in event system {eventSystemId}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError as e:
            logger.warning(f"Permission denied for user {user_id} selecting file {fileId}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            logger.error(f"Unexpected error selecting file {fileId} in event system {eventSystemId} (User {user_id}): {e}")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class DeselectFileView(APIView):
    """
    View to handle the deselecting of a file in an EventSystem.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['file manager'],
        description='Flag a file as deselected in the event system',
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
        responses={
            200: {
                'description': 'File flagged as deselected',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'file_id': {'type': 'string'}
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'EventSystem or File not found'}
        }
    )
    def patch(self, request, eventSystemId, fileId):
        """Flag a file as deselected"""
        try:
            # Log the incoming request
            logger.info(
                f"Received request to deselect file: "
                f"user_id={request.user.id}, event_system_id={eventSystemId}, file_id={fileId}"
            )

            # Deselect the file using the service
            file_reference = EventSystemFileService.flag_file(eventSystemId, fileId, request.user, action='deselect')

            # Log successful deselection
            logger.info(
                f"File deselected successfully: "
                f"file_id={file_reference.id}, user_id={request.user.id}"
            )

            # Return success response
            return Response({
                'message': 'File deselected successfully',
                'fileId': str(file_reference.id)
            }, status=status.HTTP_200_OK)

        except EventSystem.DoesNotExist:
            # Log event system not found error
            logger.error(
                f"Event system not found: event_system_id={eventSystemId}, user_id={request.user.id}"
            )
            return Response({"error": "Event system not found"}, status=status.HTTP_404_NOT_FOUND)

        except FileReference.DoesNotExist:
            # Log file not found error
            logger.error(
                f"File not found: file_id={fileId}, user_id={request.user.id}"
            )
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            # Log bad request error
            logger.warning(
                f"Bad request for deselecting file: "
                f"event_system_id={eventSystemId}, file_id={fileId}, user_id={request.user.id}, error={e}"
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError as e:
            # Log permission denied error
            logger.warning(
                f"Permission denied for deselecting file: "
                f"event_system_id={eventSystemId}, file_id={fileId}, user_id={request.user.id}, error={e}"
            )
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Unexpected error while deselecting file: "
                f"event_system_id={eventSystemId}, file_id={fileId}, user_id={request.user.id}, error={e}"
            )
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EventSystemFileListView(APIView):
    """
    Retrieve all files associated with a specific EventSystem.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['file manager'],
        description="Retrieve all files associated with a specific EventSystem.",
        parameters=[
            OpenApiParameter(
                name="eventSystemId",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="UUID of the EventSystem"
            ),
        ],
        responses={
            200: FileReferenceSerializer(many=True),
            400: {"description": "Bad request"},
            401: {"description": "Authentication required"},
            403: {"description": "Permission denied"},
            404: {"description": "EventSystem not found"},
        }
    )
    def get(self, request, eventSystemId):
        """Retrieve all files for a given EventSystem."""
        try:
            # Log the incoming request
            logger.info(
                f"Received request to retrieve files for EventSystem: "
                f"user_id={request.user.id}, event_system_id={eventSystemId}"
            )

            # Get the event system
            event_system = EventSystem.objects.get(uuid=eventSystemId)

            # Ensure user has access to the event system
            if request.user not in event_system.users.all():
                logger.warning(
                    f"Permission denied for user_id={request.user.id} to access EventSystem: "
                    f"event_system_id={eventSystemId}"
                )
                raise PermissionError("You do not have permission to view these files.")

            # Retrieve files associated with this event system
            files = event_system.file_objects.all()

            if not files.exists():
                logger.info(
                    f"No files found for EventSystem: "
                    f"event_system_id={eventSystemId}, user_id={request.user.id}"
                )
                return Response(
                    {"message": "No files associated with this EventSystem.", "files": []},
                    status=status.HTTP_200_OK,
                )

            # Log successful retrieval of files
            logger.info(
                f"Files retrieved successfully for EventSystem: "
                f"event_system_id={eventSystemId}, user_id={request.user.id}, file_count={files.count()}"
            )

            # Serialize and return the files
            serializer = FileReferenceSerializer(files, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except EventSystem.DoesNotExist:
            # Log event system not found error
            logger.error(
                f"EventSystem not found: event_system_id={eventSystemId}, user_id={request.user.id}"
            )
            return Response(
                {"error": "EventSystem not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        except PermissionError as e:
            # Log permission denied error
            logger.warning(
                f"Permission denied for user_id={request.user.id} to access EventSystem: "
                f"event_system_id={eventSystemId}, error={e}"
            )
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )

        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Unexpected error while retrieving files for EventSystem: "
                f"event_system_id={eventSystemId}, user_id={request.user.id}, error={e}"
            )
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

