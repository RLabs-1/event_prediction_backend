from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from datetime import timedelta
from django.utils import timezone

class User(AbstractBaseUser):
    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    rating = models.FloatField(default=0.0)
    num_of_usages = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    #A DateTime field to store the time when the verification code was generated.
    token_time_to_live = models.DateTimeField(null=True, blank=True)
    #A field to store the generated verification code.
    verification_code = models.CharField(max_length=6, null=True, blank=True)  # Assuming it's a 6-digit code
    #A Boolean field to track whether a password reset is pending.
    is_password_reset_pending = models.BooleanField(default=False)

    def is_token_expired(self):
        if not self.token_time_to_live:
            return True
        return timezone.now() > self.token_time_to_live + timedelta(hours=1)

    """User name should be the email"""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        """
        Return the string representation of the user, which is their email.
        """
        return self.email


    def set_password(self, raw_password):
        """
        Set the password for the user, hashing it before storing.
        """
        # Ensure the password is hashed correctly
        super().set_password(raw_password)

    def check_password(self, raw_password):
        """
        Check whether the provided password matches the stored password.
        """
        return super().check_password(raw_password)
