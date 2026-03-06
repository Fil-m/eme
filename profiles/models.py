from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class EMEUser(AbstractUser):
    bio = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='profiles/avatars/', null=True, blank=True)
    points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)

    # Mesh / Future
    telegram_id = models.CharField(max_length=100, blank=True, null=True)
    language_code = models.CharField(max_length=10, default='uk')
    is_node_admin = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    public_key = models.TextField(blank=True, null=True)  # For mesh E2E

    def __str__(self):
        return self.username

    def award_points(self, amount: int, reason: str = '') -> None:
        """Add XP points and recalculate level (every 100pts = 1 level)."""
        self.points += amount
        self.level = max(1, self.points // 100)
        self.save(update_fields=['points', 'level'])

class SocialLink(models.Model):
    user = models.ForeignKey(EMEUser, on_delete=models.CASCADE, related_name='social_links')
    network_name = models.CharField(max_length=50)
    link = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username} - {self.network_name}"


class FollowRelation(models.Model):
    follower = models.ForeignKey(EMEUser, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(EMEUser, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.username} → {self.following.username}"


class WallPost(models.Model):
    sync_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    owner = models.ForeignKey(EMEUser, on_delete=models.CASCADE, related_name='wall_posts')
    author = models.ForeignKey(EMEUser, on_delete=models.CASCADE, related_name='written_posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    likes_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.author.username} on {self.owner.username}'s wall"


class WallComment(models.Model):
    sync_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    post = models.ForeignKey(WallPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(EMEUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post.id}"
