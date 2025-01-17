from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.db import IntegrityError
from user_management.exceptions.custom_exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    InvalidUserOperationException,
)

class UserManager(BaseUserManager):
    """ Manager for the Users in the system"""

    def create_user(self, email, password=None, **extra_field):
        """Creates a user in the system"""
        if not email:
            raise ValueError("Must provide an email")
        email = self.normalize_email(email)

        try:
            user = self.model(email=email, **extra_field)
            user.set_password(password)
            user.save(using=self._db)
            return user
        except IntegrityError:
            raise UserAlreadyExistsException()


    def create_superuser(self, email, password=None):
        """Creates a superuser"""
        user = self.create_user(email, password)

        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user



class User(AbstractBaseUser, PermissionsMixin):
    """
    Base User Model
    """
    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    rating = models.FloatField(default=0.0)
    num_of_usages = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    is_password_reset_pending = models.BooleanField(default=False)
    password_reset_code = models.CharField(max_length=6, null=True, blank=True)
    password_reset_code_expiry = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)

    """User name should be the email"""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    class Meta:
        app_label = 'user_management'

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

