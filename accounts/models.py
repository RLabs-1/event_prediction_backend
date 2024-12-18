from django.db import models

# Create your models here.

# Custom User model extending Django's AbstractUser.
# This allows for adding additional fields to the user model in the future, such as phone number or address.
# Currently, the model doesn't add any extra fields but is in place for future customizations.
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom user model that extends the default Django User model.
    """
    pass