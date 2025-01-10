from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from core.models import EventSystem
from core.serializers import EventSystemCreateSerializer

class EventSystemCreateView(CreateAPIView):
    """ Creating an event system """
    queryset = EventSystem.objects.all()
    serializer_class = EventSystemCreateSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        """Set the logged-in user as the owner of the EventSystem."""
        serializer.save(user=self.request.user)