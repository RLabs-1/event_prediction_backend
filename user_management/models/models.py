from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from datetime import timedelta
from django.utils import timezone


class UserManager(BaseUserManager):
    """ Manager for the Users in the system"""

    def create_user(self, email, password=None, **extra_field):
        """Creates a user in the system"""
        if not email:
            raise ValueError("Must provide an email")
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_field)
        user.set_password(password)
        user.save(using=self._db)

        return user


    def create_superuser(self, email, password=None):
        """Creates a superuser"""
        user = self.create_user(email, password)

        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user



class User(AbstractBaseUser):
    """
    Base User Model
    """
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

    objects = UserManager()


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
