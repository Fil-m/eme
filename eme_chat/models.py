from django.db import models
from django.conf import settings
import uuid


class ChatRoom(models.Model):
    class RoomKind(models.TextChoices):
        GENERAL = 'general', 'General (Public)'
        GROUP = 'group', 'Group (Invite-only)'
        DM = 'dm', 'Direct Message'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=10, choices=RoomKind.choices, default=RoomKind.GROUP)
    title = models.CharField(max_length=255, blank=True, default='')
    avatar = models.ForeignKey(
        'eme_media.MediaFile', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='room_avatars', db_constraint=False
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='created_rooms', db_constraint=False
    )
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"[{self.kind}] {self.title or str(self.id)[:8]}"


class RoomMember(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='room_memberships', db_constraint=False
    )
    sync_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    is_muted = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('room', 'user')]
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.room} ({self.role})"


class StickerPack(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sticker_packs', db_constraint=False
    )
    name = models.CharField(max_length=100)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} by {self.owner.username}"


class Sticker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pack = models.ForeignKey(StickerPack, on_delete=models.CASCADE, related_name='stickers')
    image = models.ForeignKey(
        'eme_media.MediaFile', on_delete=models.CASCADE, related_name='stickers', db_constraint=False
    )
    label = models.CharField(max_length=100, blank=True, default='')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.label or 'Sticker'} ({self.pack.name})"


class Message(models.Model):
    class MsgType(models.TextChoices):
        TEXT = 'text', 'Text'
        STICKER = 'sticker', 'Sticker'
        IMAGE = 'image', 'Image'
        FILE = 'file', 'File'
        PIXEL = 'pixel', 'Pixel Art'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages', db_constraint=False
    )
    msg_type = models.CharField(max_length=10, choices=MsgType.choices, default=MsgType.TEXT)
    text = models.TextField(blank=True, default='')
    sticker = models.ForeignKey(
        Sticker, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages'
    )
    attachment = models.ForeignKey(
        'eme_media.MediaFile', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='chat_messages', db_constraint=False
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}@{self.room}: {self.msg_type}"


class UserActiveStickerPack(models.Model):
    """Tracks which sticker packs a user has activated"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='active_sticker_packs', db_constraint=False
    )
    pack = models.ForeignKey(StickerPack, on_delete=models.CASCADE, related_name='activated_by')

    class Meta:
        unique_together = [('user', 'pack')]


class ChatSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_settings', db_constraint=False
    )
    stickers_enabled = models.BooleanField(default=True)
    pixel_editor_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"Chat settings of {self.user.username}"
