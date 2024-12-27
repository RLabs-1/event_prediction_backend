from django.shortcuts import render

# views.py

from django.shortcuts import render

# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.services.services import UserService
from django.contrib.auth import authenticate
from user_management.services.services import JWTService

class ActivateUserView(APIView):
    def patch(self, request, userId):
        """
          Activates the user account for given user id.
        """
        service_response = UserService.activate_user(userId)
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
