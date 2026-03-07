from django.db import models
from django.conf import settings

# Create your models here.
class Bookmark(models.Model):
    url = models.URLField(max_length=2000)
    title = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # We do NOT use db_constraint=False here because we will use user_id dynamically
    user_id = models.IntegerField(db_index=True) 

    tags = models.JSONField(default=list, blank=True)
    is_favorite = models.BooleanField(default=False)

    def __str__(self):
        return self.title or self.url


class PastebinSnippet(models.Model):
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    syntax = models.CharField(max_length=50, default='plaintext')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    user_id = models.IntegerField(db_index=True, null=True, blank=True)
    
    # Optional short link like 'mbin.eme/asdf12'
    short_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.title or f"Snippet {self.id}"

class Memo(models.Model):
    user_id = models.IntegerField(db_index=True)
    content = models.TextField()
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)

    def __str__(self):
        return f"Memo {self.id} by {self.user_id}"
