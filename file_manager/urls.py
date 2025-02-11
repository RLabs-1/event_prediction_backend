from django.urls import path
from .views.views import (
    FileReferenceUpdateFileNameView,
    DeselectFileView,
    FileUploadView,
    EventSystemCreateView,
    ActivateEventSystemView,
    DeactivateEventSystemView,
    EventSystemNameUpdateView,
    FileRetrieveView,
    FileSelectView,
)

urlpatterns = [
    path('eventSystem/<uuid:eventSystemId>/files/<uuid:fileId>/', FileReferenceUpdateFileNameView.as_view(), name='file-update-filename'),
    path('eventSystem/<int:eventSystemId>/file/<int:fileId>/deselect', DeselectFileView.as_view(), name='deselect-file'),
    path('eventSystem/<int:eventSystemId>/uploadFile', FileUploadView.as_view(), name='upload-file'),
    path('user/createEventSystem/', EventSystemCreateView.as_view(), name='create-eventsystem'),
    path('eventSystem/<uuid:eventSystemId>/activate', ActivateEventSystemView.as_view(), name='activate-event-system'),
    path('eventSystem/<uuid:eventSystemId>/deactivate', DeactivateEventSystemView.as_view(), name='deactivate-event-system'),
    path('eventSystem/<uuid:eventSystemId>/files/<uuid:fileId>', FileRetrieveView.as_view(), name='get-event-system-file'),
    path('eventSystem/<uuid:eventSystemId>/', EventSystemNameUpdateView.as_view(), name='update_event_system_name'),
    path('eventSystem/<uuid:eventSystemId>/files/<uuid:fileId>/select', FileSelectView.as_view(), name='select-file'),
]