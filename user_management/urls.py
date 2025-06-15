from django.urls import path
from .views.views import (
    RegistrationView,
    UserUpdateView,
    UserLoginView,
    ResetForgotPasswordView,
    UserDeleteView,
    ForgotPasswordView,
    CurrentUserView,
    VerifyEmailView,
)
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema
from user_management.views.credentials_views import AddCredentialsView ,  UpdateCredentialView, CredentialDeleteView,GetCredentialsView
from user_management.views.eventsystem_views import EventSystemConfigurationPatchView

# Add schema for TokenRefreshView
@extend_schema(
    tags=['Authentication'],
    description='Use refresh token to get new access token',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'access': {'type': 'string', 'description': 'New access token'}
            }
        }
    }
)
class CustomTokenRefreshView(TokenRefreshView):
    pass

urlpatterns = [
    path('user/register/', RegistrationView.as_view(), name='user-register'),
    path('user/<uuid:user_id>/update/', UserUpdateView.as_view(), name='user-update'),
    path('user/<uuid:user_id>/', UserDeleteView.as_view(), name='delete-user'),
    path('user/login/', UserLoginView.as_view(), name='user-login'),
    path('user/reset-forgot-password/', ResetForgotPasswordView.as_view(), name='reset-forgot-password'),
    path('user/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('user/refresh-token/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('user/current/', CurrentUserView.as_view(), name='current-user'),
    path('user/verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('api/user/credentials/<int:credentialId>/', UpdateCredentialView.as_view(), name='update-credential'),
    path('api/user/credentials/<int:credentialId>/delete/', CredentialDeleteView.as_view(), name='delete-credential'),
    path('create-credentials/', AddCredentialsView.as_view(), name='add-credentials'),
    path('Get-credentials/<int:credentialId>/', GetCredentialsView.as_view(), name='get-credentials'),
    path('api/user/credentials', AddCredentialsView.as_view(), name='add-credentials'),
    path('api/eventSystem/<int:eventSystemId>/configuration/<int:configurationId>/', EventSystemConfigurationPatchView.as_view(), name='patch_event_system_configuration'),
]
