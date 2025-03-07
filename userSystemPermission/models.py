from django.db import models
from core.models import User, EventSystem

class UserSystemPermissions(models.Model):
    """
    Model to manage user permissions for event systems
    """
    class PermissionLevel(models.TextChoices):
        VIEWER = 'Viewer', 'Viewer'
        EDITOR = 'Editor', 'Editor'
        ADMIN = 'Admin', 'Admin'
        OWNER = 'Owner', 'Owner'

    # Remove primary_key=True from both fields
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    
    event_system = models.ForeignKey(
        EventSystem,
        on_delete=models.CASCADE,
    )
    
    permission_level = models.CharField(
        max_length=10,
        choices=PermissionLevel.choices,
        default=PermissionLevel.VIEWER
    )

    class Meta:
        # This will effectively make the combination a composite primary key
        unique_together = ('user', 'event_system')

    def __str__(self):
        return f"{self.user.email} - {self.event_system.name} - {self.permission_level}" 