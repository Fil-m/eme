from django.db import models
from profiles.models import EMEUser


PRIORITY_CHOICES = [
    ('critical', '🔴 Критичний'),
    ('high', '🟡 Високий'),
    ('medium', '🟢 Середній'),
    ('low', '⚪ Низький'),
]


class Project(models.Model):
    STATUS_CHOICES = [
        ('backlog', 'Backlog'),
        ('this_week', 'Цього тижня'),
        ('in_progress', 'В роботі'),
        ('done', 'Готово'),
        ('frozen', 'Заморожено'),
    ]
    DOMAIN_CHOICES = [
        ('life', '❤️ Особисте'),
        ('business', '💼 Бізнес'),
        ('eme', '⚡ EME'),
        ('tech', '🔧 Технічне'),
        ('community', '🤝 Спільнота'),
    ]

    owner = models.ForeignKey(EMEUser, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    emoji = models.CharField(max_length=10, default='📋')
    domain = models.CharField(max_length=20, choices=DOMAIN_CHOICES, default='eme')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='backlog')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    deadline = models.DateField(null=True, blank=True)
    next_action = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', '-updated_at']

    def __str__(self):
        return f"{self.emoji} {self.title} [{self.get_status_display()}]"


class ProjectRole(models.Model):
    """Custom role within a project — e.g. 'Шашличник', 'Координатор'"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=10, default='👤')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['project', 'name']

    def __str__(self):
        return f"{self.emoji} {self.name} ({self.project.title})"


class ProjectMember(models.Model):
    """User assigned to a project with a specific role"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(EMEUser, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.ForeignKey(ProjectRole, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'user']
        ordering = ['joined_at']

    def __str__(self):
        role_name = self.role.name if self.role else 'Учасник'
        return f"@{self.user.username} — {role_name} in {self.project.title}"


class ProjectAction(models.Model):
    """Action item / task within a project — has its own Kanban status"""
    ACTION_STATUS = [
        ('todo', '📋 Задача'),
        ('doing', '🔧 Виконується'),
        ('done', '✅ Готово'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='actions')
    text = models.CharField(max_length=500)

    # Status (replaces is_done bool)
    status = models.CharField(max_length=10, choices=ACTION_STATUS, default='todo')
    is_done = models.BooleanField(default=False)  # kept for compatibility, synced with status

    # Enriched fields
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    deadline = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)  # legacy alias

    # Dependency — this action is blocked until depends_on is done
    depends_on = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='unlocks'
    )

    # Assignee — a project member (actual person doing this)
    assignee = models.ForeignKey(
        ProjectMember, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_actions'
    )

    # Role template — if set, whoever takes this role gets auto-assigned this action
    assignee_role = models.ForeignKey(
        ProjectRole, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='role_actions'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_done', 'created_at']

    @property
    def is_blocked(self):
        return self.depends_on_id is not None and not self.depends_on.is_done

    def save(self, *args, **kwargs):
        # Keep is_done in sync with status
        self.is_done = (self.status == 'done')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{'✅' if self.is_done else '⬜'} {self.text}"
