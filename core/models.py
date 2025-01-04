from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from datetime import timedelta
from django.utils import timezone
import uuid

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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    rating = models.FloatField(default=0.0)
    num_of_usages = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    #event_systems = models.ManyToManyField('EventSystem', related_name='users')  #The EventSystem model is not yet added at the time of writing this (remove comment once its added)

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


<<<<<<< HEAD
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
    class StorageProvider(models.TextChoices):
        """
        Enum class representing different storage providers.
        Options include AWS, S3, GoogleDrive, LocalStorage, etc.
        """
        AWS = 'AWS'
        S3 = 'S3'
        GOOGLE_DRIVE = 'GoogleDrive'
        LOCAL = 'LocalStorage'

    storage_provider = models.CharField(
        max_length=20,
        choices=StorageProvider.choices,
        default=StorageProvider.LOCAL,
    )

    #Size (in bytes)
    size = models.PositiveBigIntegerField()
    #Upload Date
    upload_date = models.DateTimeField(auto_now_add=True)

    #Upload Status (ENUM)
    class UploadStatus(models.TextChoices):
        """
        Enum class representing the current status of the file upload.
        Possible values include 'Complete', 'Pending', 'Failed', and 'Processing'.
        """

        COMPLETE = 'Complete'
        PENDING = 'Pending'
        FAILED = 'Failed'
        PROCESSING = 'Processing'

    upload_status = models.CharField(
        max_length=20,
        choices=UploadStatus.choices,
        default=UploadStatus.PENDING,
    )

    #File Type (ENUM)
    class FileType(models.TextChoices):
        """
        Enum class representing the type of the file.
        Common types include 'EventFile' and 'PredictionFile'.
        """
        EVENT_FILE = 'EventFile'
        PREDICTION_FILE = 'PredictionFile'

    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.EVENT_FILE,
    )

    def __str__(self):
        """
        String representation of the FileReference model, displaying the file name and type.
         """
        return f"{self.file_name} ({self.get_file_type_display()})"
=======

class FileReference(models.Model):
    file = models.FileField(upload_to='file_references/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class EventStatus(models.TextChoices):
    ACTIVE = 'Active', 'Active'
    INACTIVE = 'Inactive', 'Inactive'

class EventSystem(models.Model):
    #A CharField for the name of the EventSystem.
    name = models.CharField(max_length=255)

    #A unique identifier for each instance, generated using Python's uuid module.
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    #A many-to-many relationship with the FileReference model to allow multiple file associations.
    file_objects = models.ManyToManyField(FileReference, related_name='event_systems')

    #An Enum field with choices of Active or Inactive, using Django's TextChoices.
    status = models.CharField(
        max_length=8,
        choices=EventStatus.choices,
        default=EventStatus.ACTIVE
    )

    # Automatically set to the current timestamp when a record is created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Automatically updated with the current timestamp whenever the record is updated.
    last_updated_at = models.DateTimeField(auto_now=True)

    #A foreign key to the User model, creating a relationship between the EventSystem and the user who owns it.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_systems')

    def __str__(self):
        return self.name
>>>>>>> 76c1d9c (Create a model for EventSystem)
