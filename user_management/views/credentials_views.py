from rest_framework import status
from rest_framework.response import Response
from user_management.serializers.credentials_serializers import CredentialsSerializer , CredentialUpdateSerializer
from user_management.services.credentials_services import create_credentials
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.model.credentials_model import Credentials
from rest_framework.generics import DestroyAPIView



class UpdateCredentialView(generics.UpdateAPIView):
    queryset = Credentials.objects.all()
    serializer_class = CredentialUpdateSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, credentialId):
        try:
            credential = Credentials.objects.get(id=credentialId)
        except Credentials.DoesNotExist:
            return Response({"error": "Credential not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CredentialUpdateSerializer(credential, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Credentials updated successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from drf_spectacular.utils import extend_schema, OpenApiResponse
from core.model.credentials_model import Credentials


class AddCredentialsView(APIView):
    """API View for adding user credentials"""

    @extend_schema(
        request=CredentialsSerializer,
        responses={
            201: CredentialsSerializer,
            400: OpenApiResponse(description="Bad Request")
        },
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
                serializer.validated_data['storage']
            )
            return Response(
                {"message": "Credentials added successfully", "id": credentials.id},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetCredentialsView(APIView):
    """API View for retrieving credentials by ID"""

    @extend_schema(
        responses={
            200: CredentialsSerializer,
            404: OpenApiResponse(description="Credentials not found")
        },
    )
    def get(self, request, credentialId):
        try:
            credentials = Credentials.objects.get(id=credentialId)
            serializer = CredentialsSerializer(credentials)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Credentials.DoesNotExist:
            return Response({"detail": "Credentials not found"}, status=status.HTTP_404_NOT_FOUND)
            sponse({"detail": "Credentials not found"}, status=status.HTTP_404_NOT_FOUND)

