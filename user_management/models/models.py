from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError
from user_management.exceptions.custom_exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    InvalidUserOperationException,
)


class UserManager(BaseUserManager):
    """Manager for the Users in the system"""

    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a user with the given email and password.
        """
        if not email:
            raise ValueError("Must provide an email")

        email = self.normalize_email(email)
        try:
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
            return user
        except IntegrityError:
            raise UserAlreadyExistsException("A user with this email already exists.")
        except Exception as e:
            raise ValidationError(f"Error creating user: {str(e)}")


    def create_superuser(self, email, password=None):
        """Creates a superuser"""
        try:
            user = self.create_user(email, password)

            user.is_staff = True
            user.is_superuser = True
            user.save(using=self._db)
        except Exception as e:      #Taking care of errors that may occur during superuser creation.
            raise ValidationError(f"Error creating superuser: {str(e)}")
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

