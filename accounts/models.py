# accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model that extends the default Django User model.
    """
    pass


class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=64)
    expiration_date = models.DateTimeField()

    def is_expired(self):
        """
        Returns True if the verification code has expired.
        """
        return timezone.now() > self.expiration_date

    def __str__(self):
        return f"Verification for {self.user.email}"
