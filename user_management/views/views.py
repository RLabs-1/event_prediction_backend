from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.services.services import RegistrationService
from user_management.serializers.serializers import RegistrationSerializer, UserUpdateSerializer
from rest_framework import generics,  permissions
from user_management.models.models import User
from user_management.services.services import UserService
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

class RegistrationView(APIView):
    def post(self, request, *args, **kwargs):
       
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
         
            user_data = serializer.validated_data
            user_service = RegistrationService()
            user = user_service.register_user(user_data)  

          
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserUpdateView(generics.RetrieveUpdateAPIView):
    """View for updating User details"""
    permission_classes = (permissions.IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    lookup_field = 'id'

    http_method_names = ['patch']

    def get_object(self):
        # Ensure the user is retrieved based on the URL parameter
        user_id = self.kwargs.get('user_id')
        return generics.get_object_or_404(User, id=user_id)





from django.shortcuts import render

# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.services.services import UserService
from django.contrib.auth import authenticate
from user_management.services.services import JWTService

class ActivateUserView(APIView):
    def patch(self, request, user_id):
        """
        Activates the user account for given user id.
        """
        service_response = UserService.activate_user(user_id)
        if service_response['success']:
            return Response(service_response, status=status.HTTP_200_OK)
        return Response(service_response, status=status.HTTP_400_BAD_REQUEST)



class UserLoginView(APIView):
    """
    Handles user login and returns a JWT token.
    """
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)


        # Authenticate user
        user = authenticate(email=email, password=password)
        if user is not None:
            tokens = JWTService.create_token(user) # Generate JWT token using JWTService
            return Response({
                "refresh": tokens["refresh"],
                "access": tokens["access"],
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
