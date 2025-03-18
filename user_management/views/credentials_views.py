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

