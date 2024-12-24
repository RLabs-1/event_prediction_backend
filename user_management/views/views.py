from django.shortcuts import render

# views.py

from django.shortcuts import render

# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.services.services import UserService


class ActivateUserView(APIView):
    def patch(self, request, userId):
        """
          Activates the user account for given user id.
        """
        service_response = UserService.activate_user(userId)
        if service_response['success']:
            return Response(service_response, status=status.HTTP_200_OK)
        return Response(service_response, status=status.HTTP_400_BAD_REQUEST)