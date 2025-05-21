from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile
from .serializers import UserProfileSerializer
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

class UserProfilePatchView(APIView):

    @extend_schema(
        request=UserProfileSerializer,
        responses=UserProfileSerializer,
        description="Partially update a user's profile settings"
    )
    def patch(self, request, userId, *args, **kwargs):
        try:
            user_profile = UserProfile.objects.get(user_id=userId)
        except UserProfile.DoesNotExist:
            raise NotFound(detail="User Profile not found")

        serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()  # Save the changes to the model
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

