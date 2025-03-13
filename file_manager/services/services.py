from core.models import EventSystem, FileReference
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class EventSystemFileService:
    @staticmethod
    def upload_file(file, event_system_id, user):
        """Save file to local storage and create a FileReference entry."""

        event_system = EventSystem.objects.get(id=event_system_id)

        # Check if the authenticated user is part of the event system
        if user not in event_system.users.all():
            raise PermissionError("You do not have permission to upload files to this EventSystem.")

        # Check if a file with the same name already exists in this event system
        existing_file = event_system.file_objects.filter(file_name=file.name).first()
        if existing_file:
            raise FileExistsError("A file with the same name already exists.")

        file_path = os.path.join('event_system', str(event_system_id), file.name)

        # Save file
        saved_path = default_storage.save(file_path, ContentFile(file.read()))
        file_url = settings.MEDIA_URL + saved_path  # Generate the file URL

        # Create FileReference entry
        file_reference = FileReference.objects.create(
            file_name=file.name,
            url=file_url,
            storage_provider=FileReference.StorageProvider.LOCAL,
            size=file.size,
            upload_status=FileReference.UploadStatus.COMPLETE,  # Mark as complete
            file_type=FileReference.FileType.EVENT_FILE
        )

        # Associate file with EventSystem
        event_system.file_objects.add(file_reference)

        return file_reference

    @staticmethod
    def delete_file(event_system_id, file_id, user):
        """Deletes a file from storage and removes its reference in the database."""

        event_system = EventSystem.objects.get(id=event_system_id)
        file_reference = FileReference.objects.get(id=file_id)

        # Check if the authenticated user is part of the event system
        if user not in event_system.users.all():
            raise PermissionError("You do not have permission to delete this file.")

        # Ensure file belongs to the event system
        if not event_system.file_objects.filter(id=file_id).exists():
            raise ValueError("File does not belong to this EventSystem.")

        # Remove the file reference from the EventSystem's Many-to-Many relationship
        event_system.file_objects.remove(file_reference)

        # Delete the file from local storage
        relative_path = file_reference.url.replace(settings.MEDIA_URL, "").lstrip("/")
        file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Remove the file reference from DB
        file_reference.delete()

        return file_id

    @staticmethod
    def update_file_name(event_system_id, file_id, new_file_name, user):
        """Update the file name for the given event system and file ID."""

        event_system = EventSystem.objects.get(id=event_system_id)
        file_reference = FileReference.objects.get(id=file_id)

        # Check if the authenticated user is part of the event system
        if user not in event_system.users.all():
            raise PermissionError("You do not have permission to update this file name.")

        # Ensure the file belongs to the event system
        if not event_system.file_objects.filter(id=file_id).exists():
            raise ValueError("File does not belong to this EventSystem.")

        # Check if the new file name is the same as the current one
        if file_reference.file_name == new_file_name:
            raise ValueError("The new file name is the same as the existing one. No update needed.")

        # Check if a file with the same name already exists in this event system
        existing_file = event_system.file_objects.filter(file_name=new_file_name).first()
        if existing_file:
            raise FileExistsError("A file with the same name already exists.")

        # Update the file name in the database
        file_reference.file_name = new_file_name

        # Rename the file in the local storage
        relative_path = file_reference.url.replace(settings.MEDIA_URL, "").lstrip("/")
        old_file_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        new_file_path = os.path.join(os.path.dirname(old_file_path), new_file_name)

        if os.path.exists(old_file_path):
            os.rename(old_file_path, new_file_path)  # Rename the file
            # Update the file URL/path in the database
            event_system_directory = os.path.join("event_system", str(event_system.uuid))
            file_reference.url = os.path.join(settings.MEDIA_URL, event_system_directory, new_file_name)
            print(f"Updated file URL: {file_reference.url}")

        # Save the updated file reference in the database
        file_reference.save()

        return file_reference

    @staticmethod
    def flag_file(event_system_id, file_id, user, action):
        """Flags a file as selected or deselected for a given event system."""

        if action not in ['select', 'deselect']:
            raise ValueError("Invalid action. Action must be either 'select' or 'deselect'.")

        event_system = EventSystem.objects.get(id=event_system_id)
        file_reference = FileReference.objects.get(id=file_id)

        # Check if the authenticated user is part of the event system
        if user not in event_system.users.all():
            raise PermissionError("You do not have permission to 'select' or 'deselect' this file.")

        # Ensure the file belongs to the event system
        if not event_system.file_objects.filter(id=file_id).exists():
            raise ValueError("File does not belong to this EventSystem.")

        # Select the file or deselect it
        if action == 'select':
            if file_reference.is_selected:
                raise ValueError("File is already selected.")
            file_reference.is_selected = True
        elif action == 'deselect':
            if not file_reference.is_selected:
                raise ValueError("File is already not selected.")
            file_reference.is_selected = False

        file_reference.save()
        return file_reference


class EventSystemService:
    @staticmethod
    def create_event_system(name, user):
        """Create a new event system and associate it with the user."""
        event_system = EventSystem.objects.create(name=name)
        event_system.users.add(user)
        return event_system

    @staticmethod
    def update_event_system_name(event_system, new_name):
        """Update the name of the EventSystem"""
        event_system.name = new_name
        event_system.save()
        return event_system

    @staticmethod
    def update_status(eventSystemId, status, user):
        """Update the status of an EventSystem (acTive/deactive)"""

        # Retrieve the EventSystem, raise ValueError if not found
        event_system = EventSystem.objects.get(id=eventSystemId)

        if user not in event_system.users.all():
            raise PermissionError("You do not have permission to deactivate this EventSystem.")

        if event_system.status == status:
            raise ValueError(f"EventSystem is already {EventSystem.EventStatus(status).label}.")

        # Update the status and save
        event_system.status = status
        event_system.save()
        return event_system



