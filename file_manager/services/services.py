from django.shortcuts import get_object_or_404
from core.models import EventSystem, FileReference


class EventSystemService:
    @staticmethod
    def create_event_system(name, user):
        """Creates a new EventSystem and associates it with the user."""

        event_system = EventSystem.objects.create(
            name=name,
            user=user
        )
        return event_system



def deselect_file(event_system_id, file_id):
    """
       Logic for deselecting a file in an EventSystem.

    """
    event_system = get_object_or_404(EventSystem, id=event_system_id)
    file = get_object_or_404(FileReference, id=file_id, event_system=event_system)

    file.selected = False
    file.save()

    return {"message": "File has been deselected"}
