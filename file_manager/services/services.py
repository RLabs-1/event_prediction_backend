from django.shortcuts import get_object_or_404
from core.models import EventSystem, FileReference
from rest_framework.exceptions import PermissionDenied, NotFound
from core.models import EventSystem, FileReference


class EventSystemFileService:
    @staticmethod
    def delete_file(event_system_id, file_id):
        try:
            # Retrieve EventSystem, raise NotFound if not found
            event_system = get_object_or_404(EventSystem, uuid=event_system_id)

            # Retrieve FileReference, raise NotFound if not found or doesn't belong to the event system
            file_reference = get_object_or_404(FileReference, uuid=file_id, event_system=event_system)

            # Proceed with deletion
            file_reference.delete()
        except EventSystem.DoesNotExist:
            raise NotFound(f"Event system with ID '{event_system_id}' not found.")
        except FileReference.DoesNotExist:
            raise NotFound(f"File with ID '{file_id}' not found in event system.")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {str(e)}")


    @staticmethod
    def select_file(event_system_id, file_id, user):
        """
        Select a file in an EventSystem
        """
        event_system = get_object_or_404(EventSystem, uuid=event_system_id)
        file = get_object_or_404(File, uuid=file_id)
        
        if not event_system.can_user_modify(user):
            raise PermissionDenied("User does not have permission to modify this event system")
        
        if file not in event_system.files.all():
            raise ValueError("File does not belong to this event system")
        
        file.is_selected = True
        file.save()
        
        return file

class EventSystemService:
    @staticmethod
    def create_event_system(name, user):
        """Creates a new EventSystem and associates it with the user."""
        event_system = EventSystem.objects.create(
            name=name,
            user=user
        )
        return event_system

    @staticmethod
    def update_status(eventSystemId, status, user):
        """Update the status of an EventSystem."""
        try:
            # Retrieve the EventSystem, raise ValueError if not found or the user doesn't have permission
            event_system = EventSystem.objects.get(uuid=eventSystemId, user=user)

            if event_system.status == status:
                raise ValueError(f"EventSystem is already {status.lower()}.")

            # Update the status and save
            event_system.status = status
            event_system.save()
            return event_system
        except EventSystem.DoesNotExist:
            raise ValueError("EventSystem not found or you do not have permission to modify it.")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {str(e)}")


def deselect_file(event_system_id, file_id):
    """
    Logic for deselecting a file in an EventSystem.
    """
    try:
        # Retrieve EventSystem, raise NotFound if not found
        event_system = get_object_or_404(EventSystem, uuid=event_system_id)

        # Retrieve FileReference, raise NotFound if not found or doesn't belong to the event system
        file_reference = get_object_or_404(FileReference, uuid=file_id, event_system=event_system)

        # Update the 'selected' flag and save
        file_reference.selected = False
        file_reference.save()

        return {"message": "File has been deselected"}
    except EventSystem.DoesNotExist:
        raise NotFound(f"Event system with ID '{event_system_id}' not found.")
    except FileReference.DoesNotExist:
        raise NotFound(f"File with ID '{file_id}' not found in event system.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {str(e)}")


class FileService:
    @staticmethod
    def get_file(event_system_id, file_id, user):
        try:
            # Retrieve EventSystem, raise NotFound if not found
            event_system = get_object_or_404(EventSystem, uuid=event_system_id)

            # Check if the user has access to the event system
            if event_system.user != user:
                raise PermissionDenied("You don't have access to this file")

            # Retrieve FileReference, raise NotFound if not found or doesn't belong to the event system
            file_reference = get_object_or_404(FileReference, uuid=file_id, event_system=event_system)
            return file_reference
        except EventSystem.DoesNotExist:
            raise NotFound(f"Event system with ID '{event_system_id}' not found.")
        except FileReference.DoesNotExist:
            raise NotFound(f"File with ID '{file_id}' not found in event system.")
        except PermissionDenied as e:
            raise e  # Re-raise PermissionDenied to be caught by the views layer
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {str(e)}")
