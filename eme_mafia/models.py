import uuid
from django.db import models


class GameRoom(models.Model):
    sync_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    STATUS_CHOICES = [
        ('lobby', 'Очікування'),
        ('night', 'Ніч'),
        ('day', 'День'),
        ('finished', 'Завершено')
    ]
    
    name = models.CharField(max_length=255)
    host = models.ForeignKey('profiles.EMEUser', on_delete=models.SET_NULL, null=True, related_name='hosted_mafia_rooms', db_constraint=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lobby')
    
    # New feature requested by user
    human_moderator = models.BooleanField(default=False)
    
    phase_number = models.IntegerField(default=0)  # e.g., 1 for Day 1 / Night 1
    phase_deadline = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class Player(models.Model):
    sync_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    ROLE_CHOICES = [
        ('unassigned', 'Без ролі'),
        ('townie', '👨‍🌾 Мирний'),
        ('mafia', '🕴️ Мафія'),
        ('doctor', '🧑‍⚕️ Лікар'),
        ('detective', '👮 Комісар'),
    ]

    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey('profiles.EMEUser', on_delete=models.CASCADE, related_name='mafia_players', db_constraint=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='unassigned')
    is_alive = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['room', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()} ({'Alive' if self.is_alive else 'Dead'})"


class GameAction(models.Model):
    sync_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    ACTION_TYPES = [
        ('vote_kill', 'Голос за вбивство (Мафія)'),
        ('vote_lynch', 'Повісити (Денне голосування)'),
        ('heal', 'Лікування (Лікар)'),
        ('inspect', 'Перевірка (Комісар)'),
    ]

    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name='actions')
    actor = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='actions_made')
    target = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True, related_name='actions_received')
    
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    phase_number = models.IntegerField(default=1)  # e.g., Night 2
    is_night_action = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.actor} -> {self.target} ({self.get_action_type_display()})"


class ChatMessage(models.Model):
    sync_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    MSG_TYPES = [
        ('public', 'Загальний'),
        ('mafia', 'Чат Мафії'),
        ('system', 'Системне'),
    ]

    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True, related_name='messages') # Null for system msgs
    
    text = models.TextField()
    msg_type = models.CharField(max_length=20, choices=MSG_TYPES, default='public')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        sender_name = self.sender.user.username if self.sender else "System"
        return f"[{self.get_msg_type_display()}] {sender_name}: {self.text[:30]}"
