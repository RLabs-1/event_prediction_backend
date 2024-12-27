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
from django.urls import path
from user_management.views.views import ActivateUserView
from drf_spectacular.views import (
    SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
)
from user_management.views.views import UserLoginView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/<int:userId>/activate', ActivateUserView.as_view(), name='activate-user'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # Schema
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),  # Swagger
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),  # redoc UI
    path('api/user/login', UserLoginView.as_view(), name='user-login'),


]



