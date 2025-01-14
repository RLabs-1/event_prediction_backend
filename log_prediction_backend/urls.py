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
from file_manager.views.views import DeselectFileView, FileUploadView, EventSystemCreateView

from drf_spectacular.views import (
    SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
)

from user_management.views.views import (
    RegistrationView, 
    UserUpdateView, 
    UserLoginView,
    ActivateUserView,
    ResetForgotPasswordView,
)

from user_management.views.views import UserDeactivateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/<int:userId>/deactivate', UserDeactivateView.as_view(), name='deactivate-user'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # Schema
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),  # Swagger
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),#redocUI
    path('api/user/register/', RegistrationView.as_view(), name='user-register'), #User registeration
    path('api/user/<int:user_id>/', UserUpdateView.as_view(), name='user-update'), # Updating User Details
    path('api/user/<int:userId>/activate', ActivateUserView.as_view(), name='activate-user'), #Endpoint to activate the user
    path('api/user/login', UserLoginView.as_view(), name='user-login'),
    path('api/user/reset-forgot-password/', ResetForgotPasswordView.as_view(), name='reset-forgot-password'),
    path('api/eventSystem/<int:eventSystemId>/file/<int:fileId>/deselect', DeselectFileView.as_view(), name='deselect-file'),
    path('api/eventSystem/<int:eventSystemId>/uploadFile', FileUploadView.as_view(), name='upload-file'),
    path('user_management/', include('user_management.urls')), #Including the user_management urls, to make the /api/user/ being recognized by Django
    path('api/user/createEventSystem/', EventSystemCreateView.as_view(), name='create-eventsystem'),

] #+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

