from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from ..exceptions.custom_exceptions import (
    UserException,
    UserValidationError,
    UserAuthenticationError,
    UserPermissionError,
    UserNotVerifiedError,
    UserStateError
)

def custom_exception_handler(exc, context):
    """Custom exception handler for User-related exceptions."""
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If unexpected error occurs
    if response is None:
        if isinstance(exc, UserException):
            data = {
                'error': exc.message,
                'code': exc.code
            }
            
            # Map exceptions to status codes
            status_code = {
                UserValidationError: status.HTTP_400_BAD_REQUEST,
                UserAuthenticationError: status.HTTP_401_UNAUTHORIZED,
                UserPermissionError: status.HTTP_403_FORBIDDEN,
                UserNotVerifiedError: status.HTTP_403_FORBIDDEN,
                UserStateError: status.HTTP_409_CONFLICT,
            }.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response(data, status=status_code)
            
    return response 