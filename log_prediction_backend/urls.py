"""
URL configuration for log_prediction_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from file_manager.views.views import FileReferenceUpdateFileNameView, DeselectFileView, FileUploadView, EventSystemCreateView, ActivateEventSystemView, DeactivateEventSystemView,EventSystemNameUpdateView ,FileRetrieveView
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView,
)
from user_management.views.views import (
    RegistrationView,
    UserUpdateView,
    UserLoginView,
    ActivateUserView,
    ResetForgotPasswordView,
    UserDeactivateView,
    VerifyEmailView,  # New Import from new code
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/eventSystem/<uuid:eventSystemId>/files/<uuid:fileId>/', FileReferenceUpdateFileNameView.as_view(), name='file-update-filename'),
    path('api/user/<int:userId>/deactivate', UserDeactivateView.as_view(), name='deactivate-user'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # Schema
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),  # Swagger
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),  # redocUI
    path('api/user/register/', RegistrationView.as_view(), name='user-register'),  # User registration
    path('api/user/<int:user_id>/', UserUpdateView.as_view(), name='user-update'),  # Updating User Details
    path('api/user/<int:userId>/activate', ActivateUserView.as_view(), name='activate-user'),  # Endpoint to activate the user
    path('api/user/login', UserLoginView.as_view(), name='user-login'),  # Login endpoint
    path('api/user/reset-forgot-password/', ResetForgotPasswordView.as_view(), name='reset-forgot-password'),  # Reset password
    path('api/eventSystem/<int:eventSystemId>/file/<int:fileId>/deselect', DeselectFileView.as_view(), name='deselect-file'),
    path('api/eventSystem/<int:eventSystemId>/uploadFile', FileUploadView.as_view(), name='upload-file'),
    path('user_management/', include('user_management.urls')),  # Include user_management URLs
    path('api/user/createEventSystem/', EventSystemCreateView.as_view(), name='create-eventsystem'),
    path('api/eventSystem/<uuid:eventSystemId>/activate', ActivateEventSystemView.as_view(), name='activate-event-system'),
    path('api/eventSystem/<uuid:eventSystemId>/deactivate', DeactivateEventSystemView.as_view(), name='deactivate-event-system'),
    path('api/eventSystem/<uuid:eventSystemId>/files/<uuid:fileId>',FileRetrieveView.as_view(),name='get-event-system-file'),
    path('api/eventSystem/<uuid:eventSystemId>/', EventSystemNameUpdateView.as_view(), name='update_event_system_name'),
    path('api/user/verifyEmail/', VerifyEmailView.as_view(), name='verify-email'),  # New Email verification endpoint

    path('', include('file_manager.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

