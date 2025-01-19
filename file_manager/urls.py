from django.urls import path
from views.views import EventSystemFileView

urlpatterns = [
    path('api/eventSystem/<uuid:eventSystemId>/files/<uuid:fileId>/', EventSystemFileView.as_view(), name='delete_event_system_file'),
]