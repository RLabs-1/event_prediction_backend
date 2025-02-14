from django.urls import path
from .views.views import (
    DeselectFileView,
    FileUploadView,
    EventSystemCreateView,
    ActivateEventSystemView,
    DeactivateEventSystemView,
    EventSystemNameUpdateView,
    FileReferenceView,
    FileSelectView,
    EventSystemFileListView,
)

urlpatterns = [
    path('eventSystem/<uuid:eventSystemId>/file/<uuid:fileId>/deselect', DeselectFileView.as_view(), name='deselect-file'),
    path('eventSystem/<uuid:eventSystemId>/uploadFile', FileUploadView.as_view(), name='upload-file'),
    path('user/createEventSystem/', EventSystemCreateView.as_view(), name='create-eventsystem'),
    path('eventSystem/<uuid:eventSystemId>/activate', ActivateEventSystemView.as_view(), name='activate-event-system'),
    path('eventSystem/<uuid:eventSystemId>/deactivate', DeactivateEventSystemView.as_view(), name='deactivate-event-system'),
    path('eventSystem/<uuid:eventSystemId>/', EventSystemNameUpdateView.as_view(), name='update_event_system_name'),
    path('eventSystem/<uuid:eventSystemId>/files/<uuid:fileId>/select', FileSelectView.as_view(), name='select-file'),
    path('eventSystem/<uuid:eventSystemId>/files/<uuid:fileId>/', FileReferenceView.as_view(), name='file-delete-get-updatename'),
    path('eventSystem/<uuid:eventSystemId>/files/', EventSystemFileListView.as_view(), name='list-event-system-files'),


]