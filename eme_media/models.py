from django.db import models
from django.conf import settings
import uuid


class Collection(models.Model):
    sync_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name', 'parent']

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class MediaFile(models.Model):
    sync_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    class Visibility(models.TextChoices):
        PRIVATE = 'private', 'Приватний'
        FRIENDS = 'friends', 'Для друзів'
        PUBLIC = 'public', 'Для всіх'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='media_files')
    file = models.FileField(upload_to='uploads/%Y/%m/%d/', blank=True, null=True)
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True, related_name='files')
    file_path = models.CharField(max_length=1024, blank=True, null=True)
    preview_path = models.CharField(max_length=1024, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.PRIVATE)
    share_token = models.CharField(max_length=64, blank=True, null=True, unique=True, db_index=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='media_files')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.file_name

    @property
    def is_image(self):
        return self.mime_type.startswith('image/')

    @property
    def is_video(self):
        return self.mime_type.startswith('video/')

    def generate_share_token(self):
        self.share_token = uuid.uuid4().hex
        self.save(update_fields=['share_token'])
        return self.share_token
