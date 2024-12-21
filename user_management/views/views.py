from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from user_management.services.services import UserService
from user_management.serializers.serializers import UserDeactivateSerializer

class UserDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, userId):
        """
        Deactivate a user by their ID.
        """
        try:
            user = UserService.deactivate_user(userId)
            serializer = UserDeactivateSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
