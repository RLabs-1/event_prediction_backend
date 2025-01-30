from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed
from loguru import logger
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


class User(AbstractBaseUser, PermissionsMixin):
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
    event_systems = models.ManyToManyField(
        'EventSystem',
        related_name='associated_users'  # Unique related name
    )
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

    # A many-to-many field to associate multiple users with the EventSystem.
    users = models.ManyToManyField(
        'User',
        related_name='event_systems_user'  # Unique related name
    )

    def __str__(self):
        return self.name
    
@receiver(post_save, sender=EventSystem)
def log_event_system_changes(sender, instance, created, **kwargs):
    try:
        if created:
            logger.debug(f"EventSystem '{instance.name}' was created with UUID {instance.uuid}.")
        else:
            logger.debug(f"EventSystem '{instance.name}' with UUID {instance.uuid} was updated.")

        if instance.status == "INVALID":
            logger.critical(f"EventSystem '{instance.name}' has entered an invalid state! Immediate attention required.")
    except Exception as e:
        logger.error(f"An error occurred while handling EventSystem '{instance.name}': {str(e)}")
        logger.critical(f"Critical failure in EventSystem '{instance.name}'. Immediate attention required!")

@receiver(m2m_changed, sender=EventSystem.file_objects.through)
def log_file_objects_changes(sender, instance, action, pk_set, **kwargs):
    try:
        if pk_set:
            files = FileReference.objects.filter(id__in=pk_set)
            file_names = [file.file_name for file in files]
            if action == "post_add":
                logger.info(f"File objects '{', '.join(file_names)}' were added to EventSystem '{instance.name}'.")
            elif action == "post_remove":
                logger.warning(f"File objects '{', '.join(file_names)}' were removed from EventSystem '{instance.name}'.")
        else:
            logger.debug(f"No file objects were affected in action '{action}' for EventSystem '{instance.name}'.")
    except Exception as e:
        logger.error(f"Error during file object change in EventSystem '{instance.name}': {str(e)}")
        logger.critical("Unexpected failure during file object changes. Investigation required.")

@receiver(m2m_changed, sender=EventSystem.users.through)
def log_user_changes(sender, instance, action, pk_set, **kwargs):
    try:
        if pk_set:
            users = User.objects.filter(id__in=pk_set)
            user_names = [user.username for user in users]
            if action == "post_add":
                logger.info(f"Users '{', '.join(user_names)}' were added to EventSystem '{instance.name}'.")
            elif action == "post_remove":
                logger.warning(f"Users '{', '.join(user_names)}' were removed from EventSystem '{instance.name}'.")
        else:
            logger.debug(f"No user changes for EventSystem '{instance.name}' during action '{action}'.")
    except Exception as e:
        logger.error(f"Error during user association in EventSystem '{instance.name}': {str(e)}")
        logger.critical("Unexpected failure during user changes. Immediate review required.")
