from django.db import models
from django.conf import settings


class CoreSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='system_settings'
    )
    # Display
    node_name = models.CharField(max_length=100, default='EME Node')
    theme = models.CharField(max_length=20, default='dark')
    language = models.CharField(max_length=10, default='uk')
    auto_update = models.BooleanField(default=True)

    # Notifications
    notification_enabled = models.BooleanField(default=True)
    notification_chat = models.BooleanField(default=True)
    notification_mesh = models.BooleanField(default=True)

    # Mesh / Node
    is_mesh_enabled = models.BooleanField(default=False)
    mesh_sync_interval = models.PositiveIntegerField(default=30, help_text='seconds')

    def __str__(self):
        return f"Settings for {self.user.username}"
