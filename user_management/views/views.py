from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics,  permissions
from user_management.services.services import RegistrationService
from user_management.serializers.serializers import RegistrationSerializer, UserUpdateSerializer
from user_management.models.models import User

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