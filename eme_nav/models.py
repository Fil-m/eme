from django.db import models
from django.conf import settings


class NavItem(models.Model):
    item_id = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=10, default='📌')
    label = models.CharField(max_length=100)
    url = models.CharField(max_length=255, blank=True, default='')
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )
    badge_count = models.IntegerField(default=0)
    visible_to_all = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.icon} {self.label}"


class UserNavAccess(models.Model):
    """Per-user visibility for nav items where visible_to_all=False."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='nav_access'
    )
    nav_item = models.ForeignKey(NavItem, on_delete=models.CASCADE, related_name='user_access')

    class Meta:
        unique_together = ['user', 'nav_item']

    def __str__(self):
        return f"{self.user.username} → {self.nav_item.label}"
