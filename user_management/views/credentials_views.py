from rest_framework import status
from rest_framework.response import Response
from user_management.serializers.credentials_serializers import CredentialsSerializer
from user_management.services.credentials_services import create_credentials
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

class AddCredentialsView(APIView):
    """API View for adding user credentials"""

    @extend_schema(
        request=CredentialsSerializer,  # This ensures Swagger knows the fields
        responses={201: CredentialsSerializer, 400: "Bad Request"},
    )

    def post(self, request):

        # Get the currently logged-in user
        user = request.user

        # Check if the user is authenticated
        if not user.is_authenticated:
            return Response({"error": "User is not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = CredentialsSerializer(data=request.data)
        if serializer.is_valid():
            credentials = create_credentials(
                serializer.validated_data['access_key'],
                serializer.validated_data['secret_key'],
                serializer.validated_data['storage'],
                user
            )
            return Response(
                {"message": "Credentials added successfully", "id": credentials.id},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
