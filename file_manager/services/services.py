from django.shortcuts import get_object_or_404
from file_manager.models import EventSystem, FileReference

class EventSystemFileService:
    @staticmethod
    def delete_file(event_system_id, file_id):
        event_system = get_object_or_404(EventSystem, uuid=event_system_id)
        file_reference = get_object_or_404(FileReference, uuid=file_id, event_system=event_system)
        file_reference.delete()

def deselect_file(event_system_id, file_id):
    """
       Logic for deselecting a file in an EventSystem.
    """
    event_system = get_object_or_404(EventSystem, uuid=event_system_id)
    file_reference = get_object_or_404(FileReference, uuid=file_id, event_system=event_system)
    file_reference.selected = False
    file_reference.save()
    return {"message": "File has been deselected"}
