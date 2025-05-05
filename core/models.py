from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from datetime import timedelta
from django.utils import timezone
import uuid
from user_management.exceptions.custom_exceptions import (
    UserValidationError,
    UserStateError,
    UserNotVerifiedError
)
from core.model.credentials_model import Credentials

class UserManager(BaseUserManager):
    """ Manager for the Users in the system"""

    def create_user(self, email, password=None, **extra_fields):
        """Creates a user in the system"""
        if not email:
            raise ValueError("Must provide an email")
        email = self.normalize_email(email)

        # Set default values for is_active
        extra_fields.setdefault('is_active', True)  # Users start as active by default
        
        user = self.model(
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, name=None, **extra_fields):
        """Creates a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)  # Superusers are always active

        if not name:
            name = email

        return self.create_user(
            email=email,
            password=password,
            name=name,
            **extra_fields
        )

class User(AbstractBaseUser, PermissionsMixin):
    """
    Base User Model
    """
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text="Unique identifier for the user"
    )

    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(
        default=False,
        help_text='Designates whether this user is logged in. Set False when user logs out.'
    )
    rating = models.FloatField(default=0.0)
    num_of_usages = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    event_systems = models.ManyToManyField(
        'EventSystem',
        related_name='associated_users'
    )
    is_deleted = models.BooleanField(default=False)
    is_password_reset_pending = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)


    credentials = models.ManyToManyField(
        Credentials,
        related_name="users",
        blank=True  # means users may not have credentials initially
    )


    def is_token_expired(self):
        """Check if the verification code has expired"""
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
    
      # Add unique related_name arguments
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_user_permissions',
        blank=True,
    )
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_user_groups',
        blank=True,
    )

    class Meta:
        app_label = 'core'

    def clean(self):
        """Validate user data"""
        if not self.email:
            raise UserValidationError("Email is required")
        if not self.name:
            raise UserValidationError("Name is required")

    def save(self, *args, **kwargs):
        try:
            self.clean()
            super().save(*args, **kwargs)
        except Exception as e:
            raise UserStateError(f"Error saving user: {str(e)}")

class FileReference(models.Model):
    """
    A model to store metadata about uploaded files in the system.
    This includes unique identification, file details, storage information, and processing status.
    """
    #A unique identifier for the file, generated using UUID.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #The name of the file as it was uploaded or renamed.
    file_name = models.CharField(max_length=255)
    #The URL where the file is stored or can be accessed.
    url = models.URLField(max_length=500)

    #Storage Provider (ENUM)
    class StorageProvider(models.IntegerChoices):
        AWS = 1, 'AWS'
        S3 = 2, 'S3'
        GOOGLE_DRIVE = 3, 'Google Drive'
        LOCAL = 4, 'Local Storage'
        SCP = 5, 'SCP'

    storage_provider = models.IntegerField(
        choices=StorageProvider.choices,
        default=StorageProvider.LOCAL
    )

    #Size (in bytes)
    size = models.PositiveBigIntegerField()
    #Upload Date
    upload_date = models.DateTimeField(auto_now_add=True)

    #Upload Status (ENUM)
    class UploadStatus(models.IntegerChoices):
        COMPLETE = 1, 'Complete'
        PENDING = 2, 'Pending'
        FAILED = 3, 'Failed'
        PROCESSING = 4, 'Processing'

    upload_status = models.IntegerField(
        choices=UploadStatus.choices,
        default=UploadStatus.PENDING
    )

    #File Type (ENUM)
    class FileType(models.IntegerChoices):
        EVENT_FILE = 1, 'Event File'
        PREDICTION_FILE = 2, 'Prediction File'

    file_type = models.IntegerField(
        choices=FileType.choices,
        default=FileType.EVENT_FILE
    )

    is_selected = models.BooleanField(default=False)

    def __str__(self):
        """
        String representation of the FileReference model, displaying the file name and type.
         """
        return f"{self.file_name} ({self.get_file_type_display()})"

class EventSystem(models.Model):
    #A CharField for the name of the EventSystem.
    name = models.CharField(max_length=255)

    #A unique identifier for each instance, generated using Python's uuid module.
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)

    #A many-to-many relationship with the FileReference model to allow multiple file associations.
    file_objects = models.ManyToManyField(FileReference, related_name='event_systems')

    class EventStatus(models.IntegerChoices):
        ACTIVE = 1, 'Active'
        INACTIVE = 2, 'Inactive'

    #An Enum field with choices of Active or Inactive.
    status = models.IntegerField(
        choices=EventStatus.choices,
        default=EventStatus.ACTIVE
    )

    # Automatically set to the current timestamp when a record is created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Automatically updated with the current timestamp whenever the record is updated.
    last_updated_at = models.DateTimeField(auto_now=True)

    # A many-to-many field to associate multiple users with the EventSystem.
    users = models.ManyToManyField(
        'User',
        related_name='event_systems_user'  # Unique related name
    )

    def __str__(self):
        return self.name

class UserToken(models.Model):
    """Model to store user tokens"""
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='tokens'
    )
    access_token = models.TextField()
    refresh_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'

    def __str__(self):
        return f"Token for {self.user.email}"

    


class EmailVerification(models.Model):
    """
    Model to handle the email verification process for users.
    """
    email = models.EmailField(primary_key=True, max_length=255, default="default@example.com") # Lookup the table using email instead of user_id
    verification_code = models.CharField(max_length=6, null=True)  # Store the verification code 
    token_time_to_live = models.DateTimeField(null=True)  # The time when the code will expire
    tries_left = models.IntegerField(default=3)  # Number of verification attempts left (3 tries per code by default)
    
    def is_token_expired(self):
        """Check if the verification code has expired"""
        if not self.token_time_to_live:
            return True
        return timezone.now() > self.token_time_to_live + timedelta(hours=1)
    
    def decrement_tries(self):
        """Decrement the number of tries left."""
        if self.tries_left > 0:
            self.tries_left -= 1
            self.save()
    
    def delete_oldcode(self):
        """Delete the old verification code."""
        if(self.tries_left<=0):
            self.verification_code=None
            self.token_time_to_live=None
            self.tries_left=0
            self.save()


    
    def reset_code(self, new_code, ttl):
        """Reset the verification code and ttl."""
        self.verification_code = new_code
        self.token_time_to_live = ttl
        self.tries_left = 3  # Reset tries to 3
        self.save()

    def __str__(self):
        return f"Verification for {self.user.email}"

    class Meta:
        verbose_name = 'Email Verification'
        verbose_name_plural = 'Email Verifications'



class UserSystemPermissions(models.Model):
    """
    Model to manage user permissions for event systems
    """

    class PermissionLevel(models.IntegerChoices):
        VIEWER = 1, 'Viewer'
        EDITOR = 2, 'Editor'
        ADMIN = 3, 'Admin'
        OWNER = 4, 'Owner'

    # Remove primary_key=True from both fields
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    event_system = models.ForeignKey(
        EventSystem,
        on_delete=models.CASCADE,
    )

    permission_level = models.IntegerField(
        choices=PermissionLevel.choices,
        default=PermissionLevel.VIEWER
    )

    class Meta:
        # This will effectively make the combination a composite primary key
        unique_together = ('user', 'event_system')

    def __str__(self):
        return f"{self.user.email} - {self.event_system.name} - {self.get_permission_level_display()}"

