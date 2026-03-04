"""
EME AI Module Models
Keeps a log of all AI requests for auditing and rate limiting.
"""
from django.db import models
from profiles.models import EMEUser


class AIRequest(models.Model):
    """Log every AI call — module, user, cost, result."""
    MODULE_CHOICES = [
        ('projects', 'Projects'),
        ('network', 'Network'),
        ('generic', 'Generic'),
    ]
    STATUS_CHOICES = [
        ('ok', 'Success'),
        ('error', 'Error'),
        ('timeout', 'Timeout'),
    ]

    user = models.ForeignKey(EMEUser, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='ai_requests')
    module = models.CharField(max_length=50, choices=MODULE_CHOICES, default='generic')
    provider = models.CharField(max_length=50, default='ollama')
    model = models.CharField(max_length=100, default='llama3')
    prompt_preview = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ok')
    error_msg = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.provider}] {self.module} by {self.user} — {self.status}"
