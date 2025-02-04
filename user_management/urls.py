from django.urls import path
from .views.views import (
    RegistrationView,
    UserUpdateView,
    UserLoginView,
    ActivateUserView,
    ResetForgotPasswordView,
    UserDeactivateView,
    ForgotPasswordView,
    UserLogoutView,
    CurrentUserView,
)
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema

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
    path('user/<int:user_id>/update/', UserUpdateView.as_view(), name='user-update'),
    path('user/<int:user_id>/activate/', ActivateUserView.as_view(), name='activate-user'),
    path('user/<int:userId>/deactivate', UserDeactivateView.as_view(), name='deactivate-user'),
    path('user/login', UserLoginView.as_view(), name='user-login'),
    path('user/logout/', UserLogoutView.as_view(), name='user-logout'),
    path('user/reset-forgot-password/', ResetForgotPasswordView.as_view(), name='reset-forgot-password'),
    path('user/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('user/refresh-token/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('user/current/', CurrentUserView.as_view(), name='current-user'),
]
