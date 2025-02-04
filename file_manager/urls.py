from django.urls import path
from views.views import EventSystemFileView, SelectFileView

urlpatterns = [
    path('api/eventSystem/<uuid:eventSystemId>/files/<uuid:fileId>/', EventSystemFileView.as_view(), name='delete_event_system_file'),
    path('api/eventSystem/<uuid:eventSystemId>/files/<uuid:fileId>/select', SelectFileView.as_view(), name='select-file'),
]