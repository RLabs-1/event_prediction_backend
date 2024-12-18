# accounts/urls.py

from django.urls import path
from .views import register_user, verify_email

urlpatterns = [
    path('api/user/register/', register_user, name='register_user'),
    path('verify-email/', verify_email, name='verify_email'),
]
