from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_management.services.services import RegistrationService
from user_management.serializers.serializers import RegistrationSerializer

class RegistrationView(APIView):
    def post(self, request, *args, **kwargs):
       
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
         
            user_data = serializer.validated_data
            user_service = RegistrationService()
            user = user_service.register_user(user_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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

          
            

