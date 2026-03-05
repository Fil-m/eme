from django.db import models
from django.conf import settings

class Player(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='park_player')
    username = models.CharField(max_length=100)
    
    # Resources
    wood = models.IntegerField(default=0)
    iron = models.IntegerField(default=0)
    gold = models.IntegerField(default=0)
    
    # Buildings
    castle = models.IntegerField(default=0)
    forge = models.IntegerField(default=0)
    magic = models.IntegerField(default=0)
    
    # Combat Stats
    life = models.IntegerField(default=100)
    dragon_life = models.IntegerField(default=100)
    score = models.IntegerField(default=0)
    
    # Items
    shield = models.IntegerField(default=0)
    magic_shield = models.IntegerField(default=0)
    sword = models.IntegerField(default=0)
    magic_sword = models.IntegerField(default=0)
    elixir = models.IntegerField(default=0)
    flash = models.IntegerField(default=0)
    
    log = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Player: {self.username} (User: {self.user.username})"


class PlayerStatus(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='status')
    can_play = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.player.username} - Can Play: {self.can_play}"
