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

