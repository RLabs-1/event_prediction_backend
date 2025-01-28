from django.db import models
from django.contrib.auth.models import get_user_model

User = get_user_model()

 # Permission level
PERMISSION_CHOICES = [
        ('R', 'Read'),
        ('W', 'Write'),
        ('A', 'Admin'),
    ]

class UserSystemPermissions(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    event_system = models.CharField(max_length=100)

    permission_level = models.CharField(max_length=1, choices=PERMISSION_CHOICES)

    class Meta:
        # Composite primary key
        unique_together = ('user', 'event_system')
        # Optional: Custom table name
        db_table = 'user_system_permissions'

    def __str__(self):
        return f"{self.user} - {self.event_system} - {self.permission_level}"
# Create your models here.
