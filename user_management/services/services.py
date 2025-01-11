from django.shortcuts import get_object_or_404
from user_management.models import EventSystem, FileReference

class EventSystemFileService:
    @staticmethod
    def delete_file(event_system_id, file_id):
        event_system = get_object_or_404(EventSystem, uuid=event_system_id)
        file_reference = get_object_or_404(FileReference, uuid=file_id, event_system=event_system)
        file_reference.delete()
