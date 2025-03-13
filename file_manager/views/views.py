from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
import os
from rest_framework.permissions import IsAuthenticated

from core.models import EventSystem, EventStatus, FileReference, UserSystemPermissions
from file_manager.services.services import EventSystemService, EventSystemFileService
from file_manager.serializers.serializers import EventSystemNameUpdateSerializer, FileReferenceSerializer, EventSystemCreateSerializer

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
                    'id': {'type': 'string', 'format': 'uuid'}
                }
            },
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            403: {'description': "Permission Denied"}
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
        serializer = EventSystemCreateSerializer(data=request.data)

        if serializer.is_valid():
            try:
                event_system = EventSystemService.create_event_system(
                    serializer.validated_data['name'], request.user
                )
                return Response(
                    {'id': event_system.id},
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"error": "Something went wrong while creating the event system."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
            204: {},
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied - You do not have permission to update this EventSystem.'},
            404: {'description': 'EventSystem not found'},
            500: {'description': 'An unexpected error occurred. Please try again later.'}
        }
    )
    def patch(self, request, eventSystemId):
        try:

            event_system = EventSystem.objects.get(id=eventSystemId)

            # Check if the user is authorized to update this EventSystem
            if request.user not in event_system.users.all():
                raise PermissionError("Permission denied – You do not have permission to update this EventSystem.")

            # Use serializer for validation
            serializer = EventSystemNameUpdateSerializer(event_system, data=request.data, partial=True)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Ensure 'name' exists in validated data
            if 'name' not in serializer.validated_data:
                raise ValueError("Invalid request. 'name' field is required.")

            updated_event_system = EventSystemService.update_event_system_name(event_system, serializer.validated_data['name'])
            return Response(status=status.HTTP_204_NO_CONTENT)

        except EventSystem.DoesNotExist:
            return Response({"error": "Event system not found"}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ActivateEventSystemView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=['file manager'],
        description='Activate an EventSystem.',
        request=None,
        responses={
            204: {},
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
            # Attempt to update the status of the EventSystem
            event_system = EventSystemService.update_status(eventSystemId, EventStatus.ACTIVE, request.user)
            return Response({
                "message": "EventSystem activated successfully."
            }, status=status.HTTP_204_NO_CONTENT)

        except ValueError as e:
            # Handle invalid values or data
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except EventSystem.DoesNotExist:
            # Handle cases where the EventSystem ID does not exist
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)

        except PermissionError:
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
        request=None,
        responses={
            204: {},
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
        print("Trying to patch")
        try:
            # Attempt to update the status of the EventSystem
            event_system = EventSystemService.update_status(eventSystemId, EventStatus.INACTIVE, request.user)
            return Response( status=status.HTTP_204_NO_CONTENT)

        except ValueError as e:
            # Handle invalid values or data
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except EventSystem.DoesNotExist:
            # Handle cases where the EventSystem ID does not exist
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)

        except PermissionError as e:
            # Handle permission-related errors
            return Response({"error": "You do not have permission to deactivate this EventSystem."},
                            status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred. Please try again later."+ str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
            201: {
                'description': 'File uploaded successfully',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'file_id': {'type': 'string'},
                }
            },
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

        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            file_reference = EventSystemFileService.upload_file(file, eventSystemId, request.user)

            return Response({
                "message": "File uploaded successfully",
                "file_id": file_reference.id
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except EventSystem.DoesNotExist:
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)

        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except FileExistsError:
            # Handle cases where a file with the same name already exists
            return Response(
                {'error': 'A file with the same name already exists. Please use a unique filename.'},
                status=status.HTTP_409_CONFLICT
            )

        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class FileReferenceView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=['file manager'],
        description='Deleting a file',
        responses={
            204: {},
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'File or EventSystem not found'},
        }
    )
    def delete(self, request, eventSystemId, fileId):
        """Delete file from event system"""
        try:
            EventSystemFileService.delete_file(eventSystemId, fileId, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except EventSystem.DoesNotExist:
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)

        except FileReference.DoesNotExist:
            return Response({"error": "FileReference not found."}, status=status.HTTP_404_NOT_FOUND)

        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred. Please try again later."+str(e)},
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
            200: FileReferenceSerializer,
            400: {'description': 'File does not belong to the EventSystem'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'File or event system not found'},
        }
    )
    def get(self, request, eventSystemId, fileId):
        """Retrieve a file from event system"""
        try:
            event_system = EventSystem.objects.get(id=eventSystemId)
            file_reference = FileReference.objects.get(id=fileId)

            try:
                user_permission = UserSystemPermissions.objects.get(user=request.user, event_system=event_system)
            except UserSystemPermissions.DoesNotExist:
                raise PermissionError("You do not have access to this file.")

            # Define allowed roles (Admins, Owners, Viewers)
            allowed_roles = {
                UserSystemPermissions.PermissionLevel.ADMIN,
                UserSystemPermissions.PermissionLevel.OWNER,
                UserSystemPermissions.PermissionLevel.VIEWER
            }

            if user_permission.permission_level not in allowed_roles:
                raise PermissionError("You do not have permission to retrieve this file.")

            # Ensure file belongs to the event system
            if not event_system.file_objects.filter(id=fileId).exists():
                raise ValueError("File does not belong to this EventSystem.")
            serializer = FileReferenceSerializer(file_reference)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except EventSystem.DoesNotExist:
            return Response({"error": "Event system not found"}, status=status.HTTP_404_NOT_FOUND)

        except FileReference.DoesNotExist:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
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
            204: {},
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

            updated_file = EventSystemFileService.update_file_name(eventSystemId, fileId, new_file_name, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except EventSystem.DoesNotExist:
            return Response({"error": "Event system not found"}, status=status.HTTP_404_NOT_FOUND)

        except FileReference.DoesNotExist:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except FileExistsError:
            # Handle cases where a file with the same name already exists
            return Response(
                {'error': 'A file with the same name already exists. Please use a unique filename.'},
                status=status.HTTP_409_CONFLICT
            )

        except Exception as e:
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
            204: {},
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'File or event system not found'},
        }
    )
    def patch(self, request, eventSystemId, fileId):
        """Flag a file as selected"""
        try:

            EventSystemFileService.flag_file(eventSystemId, fileId, request.user, action='select')

            return Response(status=status.HTTP_204_NO_CONTENT)

        except EventSystem.DoesNotExist:
            return Response({"error": "Event system not found"},status=status.HTTP_404_NOT_FOUND)

        except FileReference.DoesNotExist:
            return Response({"error": "File not found"},status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:return Response({"error": str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            204: {},
            400: {'description': 'Bad request'},
            401: {'description': 'Authentication required'},
            403: {'description': 'Permission denied'},
            404: {'description': 'EventSystem or File not found'}
        }
    )
    def patch(self, request, eventSystemId, fileId):
        """Flag a file as deselected"""
        try:
            file_reference = EventSystemFileService.flag_file(eventSystemId, fileId, request.user, action='deselect')

            return Response({
                'message': 'File deselected successfully'
            }, status=status.HTTP_204_NO_CONTENT)

        except EventSystem.DoesNotExist:
            return Response({"error": "Event system not found"}, status=status.HTTP_404_NOT_FOUND)

        except FileReference.DoesNotExist:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
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
            # Get the event system
            event_system = EventSystem.objects.get(id=eventSystemId)

            try:
                user_permission = UserSystemPermissions.objects.get(user=request.user, event_system=event_system)
            except UserSystemPermissions.DoesNotExist:
                raise PermissionError("You do not have permission to view files.")

            allowed_roles = {
                UserSystemPermissions.PermissionLevel.ADMIN,
                UserSystemPermissions.PermissionLevel.OWNER,
                UserSystemPermissions.PermissionLevel.VIEWER
            }

            if user_permission.permission_level not in allowed_roles:
                raise PermissionError("You do not have permission to view files.")

            # Retrieve files associated with this event system
            files = event_system.file_objects.all()

            if not files.exists():
                return Response(
                    {"message": "No files associated with this EventSystem.", "files": []},
                    status=status.HTTP_200_OK,
                )

            serializer = FileReferenceSerializer(files, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except EventSystem.DoesNotExist:
            return Response({"error": "EventSystem not found."},status=status.HTTP_404_NOT_FOUND,)

        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

