from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
import os
from rest_framework.permissions import IsAuthenticated
from loguru import logger  # Use loguru instead of standard logging

from core.models import EventSystem, FileReference, UserSystemPermissions
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
        logger.debug(f"Received POST request to create event system from user: {request.user.email}")

        serializer = EventSystemCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                logger.debug(f"Serializer validated data: {serializer.validated_data}")
                event_system = EventSystemService.create_event_system(
                    serializer.validated_data['name'], request.user
                )
                logger.info(f"Successfully created event system with ID: {event_system.id} by user: {request.user.email}")

                return Response(
                    {'id': event_system.id},
                    status=status.HTTP_201_CREATED
                )

            except Exception as e:
                logger.error(f"Critical error while creating event system: {str(e)}")
                logger.exception("Full traceback:")  # This will log the full traceback
                return Response(
                    {"error": "Something went wrong while creating the event system."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        logger.warning(f"Invalid request data from user {request.user.email}: {serializer.errors}")
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
            logger.debug(f"Attempting to update event system name. ID: {eventSystemId}, User: {request.user.email}")
            event_system = EventSystem.objects.get(id=eventSystemId)

        
            user_permission = UserSystemPermissions.objects.get(user=request.user, event_system=event_system)
            allowed_roles = {
                 UserSystemPermissions.PermissionLevel.ADMIN,
                 UserSystemPermissions.PermissionLevel.OWNER,
                 UserSystemPermissions.PermissionLevel.EDITOR
             }
        
            if user_permission.permission_level not in allowed_roles:
                 logger.warning(f"Permission denied - User {request.user.email} attempted to update event system {eventSystemId}")
                 raise PermissionError("You do not have permission to do this action.")
              
          


            serializer = EventSystemNameUpdateSerializer(event_system, data=request.data, partial=True)

            if not serializer.is_valid():
                logger.warning(f"Invalid data for event system update: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            if 'name' not in serializer.validated_data:
                logger.error("Name field missing in request")
                raise ValueError("Invalid request. 'name' field is required.")

            updated_event_system = EventSystemService.update_event_system_name(
                event_system, 
                serializer.validated_data['name']
            )
            logger.info(f"Successfully updated event system name. ID: {eventSystemId}, New name: {serializer.validated_data['name']}")
            return Response(status=status.HTTP_204_NO_CONTENT)


        except UserSystemPermissions.DoesNotExist:
            return Response({"error": "User permissions not found"}, status=status.HTTP_403_FORBIDDEN)
        
        except EventSystem.DoesNotExist:
            logger.error(f"Event system not found. ID: {eventSystemId}")
            return Response({"error": "Event system not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            logger.warning(f"Value error while updating event system: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            logger.warning(f"Permission error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.exception("Unexpected error while updating event system name")
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

            event_system = EventSystem.objects.get(id=eventSystemId)
            user_permission = UserSystemPermissions.objects.get(user=request.user, event_system=event_system)
            allowed_roles = {
                 UserSystemPermissions.PermissionLevel.ADMIN,
                 UserSystemPermissions.PermissionLevel.OWNER
             }
        
            if user_permission.permission_level not in allowed_roles:
                 raise PermissionError("You do not have permission to do this action.")
              
              
            logger.debug(f"Attempting to activate event system. ID: {eventSystemId}, User: {request.user.email}")
            
            # Attempt to update the status of the EventSystem
            event_system = EventSystemService.update_status(eventSystemId, EventSystem.EventStatus.ACTIVE, request.user)
            
            logger.info(f"Successfully activated event system. ID: {eventSystemId}")
            return Response( status=status.HTTP_204_NO_CONTENT)
            
        
        
        except UserSystemPermissions.DoesNotExist:
            return Response({"error": "User permissions not found"}, status=status.HTTP_403_FORBIDDEN)
        

        except ValueError as e:
            logger.warning(f"Invalid request for event system activation: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except EventSystem.DoesNotExist:
            logger.error(f"Event system not found for activation. ID: {eventSystemId}")
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            logger.warning(f"Permission denied for event system activation. User: {request.user.email}, ID: {eventSystemId}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.exception("Unexpected error during event system activation")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        try:

            event_system = EventSystem.objects.get(id=eventSystemId)
            user_permission = UserSystemPermissions.objects.get(user=request.user, event_system=event_system)
            allowed_roles = {
                 UserSystemPermissions.PermissionLevel.ADMIN,
                 UserSystemPermissions.PermissionLevel.OWNER
             }
        
            if user_permission.permission_level not in allowed_roles:
                 raise PermissionError("You do not have permission to do this action.")
            
            logger.debug(f"Attempting to deactivate event system. ID: {eventSystemId}, User: {request.user.email}")
            
            # Attempt to update the status of the EventSystem
            event_system = EventSystemService.update_status(eventSystemId, EventSystem.EventStatus.INACTIVE, request.user)
            
            logger.info(f"Successfully deactivated event system. ID: {eventSystemId}")
            
            return Response( status=status.HTTP_204_NO_CONTENT)



        except UserSystemPermissions.DoesNotExist:
            return Response({"error": "User permissions not found"}, status=status.HTTP_403_FORBIDDEN)
        
        except ValueError as e:
            logger.warning(f"Invalid request for event system deactivation: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except EventSystem.DoesNotExist:
            logger.error(f"Event system not found for deactivation. ID: {eventSystemId}")
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            logger.warning(f"Permission denied for event system deactivation. User: {request.user.email}, ID: {eventSystemId}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.exception("Unexpected error during event system deactivation")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            logger.warning(f"File upload attempted without file. User: {request.user.email}")
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            logger.debug(f"Attempting to upload file. Name: {file.name}, Size: {file.size}, User: {request.user.email}")
            file_reference = EventSystemFileService.upload_file(file, eventSystemId, request.user)

            logger.info(f"Successfully uploaded file. ID: {file_reference.id}, Name: {file.name}")
            return Response({
                "message": "File uploaded successfully",
                "file_id": file_reference.id
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            logger.warning(f"Invalid file upload request: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except EventSystem.DoesNotExist:
            logger.error(f"Event system not found for file upload. ID: {eventSystemId}")
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            logger.warning(f"Permission denied for file upload. User: {request.user.email}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except FileExistsError:
            logger.warning(f"Duplicate file name detected: {file.name}")
            return Response(
                {'error': 'A file with the same name already exists.'},
                status=status.HTTP_409_CONFLICT
            )
        except Exception as e:
            logger.exception(f"Unexpected error during file upload: {file.name}")
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            logger.debug(f"Attempting to delete file. ID: {fileId}, Event System: {eventSystemId}, User: {request.user.email}")
            EventSystemFileService.delete_file(eventSystemId, fileId, request.user)
            logger.info(f"Successfully deleted file. ID: {fileId}")
            return Response(status=status.HTTP_204_NO_CONTENT)

        except ValueError as e:
            logger.warning(f"Invalid file deletion request: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except EventSystem.DoesNotExist:
            logger.error(f"Event system not found for file deletion. ID: {eventSystemId}")
            return Response({"error": "EventSystem not found."}, status=status.HTTP_404_NOT_FOUND)
        except FileReference.DoesNotExist:
            logger.error(f"File not found for deletion. ID: {fileId}")
            return Response({"error": "FileReference not found."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            logger.warning(f"Permission denied for file deletion. User: {request.user.email}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.exception("Unexpected error during file deletion")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            logger.debug(f"Attempting to select file. ID: {fileId}, Event System: {eventSystemId}, User: {request.user.email}")
            EventSystemFileService.flag_file(eventSystemId, fileId, request.user, action='select')
            logger.info(f"Successfully selected file. ID: {fileId}")
            return Response(status=status.HTTP_204_NO_CONTENT)

        except EventSystem.DoesNotExist:
            logger.error(f"Event system not found for file selection. ID: {eventSystemId}")
            return Response({"error": "Event system not found"},status=status.HTTP_404_NOT_FOUND)

        except FileReference.DoesNotExist:
            logger.error(f"File not found for selection. ID: {fileId}")
            return Response({"error": "File not found"},status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            logger.warning(f"Invalid file selection request: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError as e:
            logger.warning(f"Permission denied for file selection. User: {request.user.email}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            logger.exception("Unexpected error during file selection")
            return Response({"error": str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            logger.debug(f"Attempting to deselect file. ID: {fileId}, Event System: {eventSystemId}, User: {request.user.email}")
            file_reference = EventSystemFileService.flag_file(eventSystemId, fileId, request.user, action='deselect')
            logger.info(f"Successfully deselected file. ID: {fileId}")
            return Response(status=status.HTTP_204_NO_CONTENT)

        except EventSystem.DoesNotExist:
            logger.error(f"Event system not found for file deselection. ID: {eventSystemId}")
            return Response({"error": "Event system not found"}, status=status.HTTP_404_NOT_FOUND)

        except FileReference.DoesNotExist:
            logger.error(f"File not found for deselection. ID: {fileId}")
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            logger.warning(f"Invalid file deselection request: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except PermissionError as e:
            logger.warning(f"Permission denied for file deselection. User: {request.user.email}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            logger.exception("Unexpected error during file deselection")
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
            logger.debug(f"Attempting to list files for event system. ID: {eventSystemId}, User: {request.user.email}")
            
            # Get the event system
            event_system = EventSystem.objects.get(id=eventSystemId)

            try:
                user_permission = UserSystemPermissions.objects.get(user=request.user, event_system=event_system)
                
                allowed_roles = {
                    UserSystemPermissions.PermissionLevel.ADMIN,
                    UserSystemPermissions.PermissionLevel.OWNER,
                    UserSystemPermissions.PermissionLevel.VIEWER
                }

                if user_permission.permission_level not in allowed_roles:
                    logger.warning(f"Insufficient permissions for user {request.user.email} to list files")
                    raise PermissionError("You do not have permission to view files.")
                    
            except UserSystemPermissions.DoesNotExist:
                logger.warning(f"Permission denied - User {request.user.email} attempted to list files for event system {eventSystemId}")
                raise PermissionError("You do not have permission to view files.")


            # Retrieve files associated with this event system
            files = event_system.file_objects.all()

            if not files.exists():
                logger.info(f"No files found for event system {eventSystemId}")
                return Response(
                    {"message": "No files associated with this EventSystem.", "files": []},
                    status=status.HTTP_200_OK,
                )

            serializer = FileReferenceSerializer(files, many=True)
            logger.info(f"Successfully retrieved {files.count()} files for event system {eventSystemId}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except EventSystem.DoesNotExist:
            logger.error(f"Event system not found for file listing. ID: {eventSystemId}")
            return Response(
                {"error": "EventSystem not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

            

        except PermissionError as e:
            logger.warning(f"Permission error during file listing: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)


        except Exception as e:
            logger.exception("Unexpected error during file listing")
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
