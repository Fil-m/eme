from django.db import models

class KBCategory(models.Model):
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=10, default="📁")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "KB Categories"

    def __str__(self):
        return f"{self.emoji} {self.name}"

class KBArticle(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.ForeignKey(KBCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    tags = models.CharField(max_length=255, blank=True, help_text="Comman separated tags")
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', '-updated_at']

    def __str__(self):
        return self.title
