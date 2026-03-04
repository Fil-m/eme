from django.db import models
from django.conf import settings
import uuid


class Node(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='nodes'
    )
    name = models.CharField(max_length=255, blank=True, default='')
    device_id = models.CharField(max_length=255, blank=True, default='')
    ip_address = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name or self.device_id} ({self.user.username})"


class ChatRoom(models.Model):
    class RoomType(models.TextChoices):
        DM = 'dm', 'Direct Message'
        GROUP = 'group', 'Group Chat'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True, default='')
    room_type = models.CharField(max_length=10, choices=RoomType.choices, default=RoomType.DM)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='chat_rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or f"Room {str(self.id)[:8]}"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages'
    )
    text = models.TextField(blank=True, default='')
    attachment = models.ForeignKey(
        'eme_media.MediaFile', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='messages'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.text[:30]}"
