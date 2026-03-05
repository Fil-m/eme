from rest_framework import serializers
from .models import Player, PlayerStatus

class PlayerSerializer(serializers.ModelSerializer):
    can_play = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            'id', 'username', 'wood', 'iron', 'gold',
            'castle', 'forge', 'magic', 'life', 'dragon_life',
            'score', 'shield', 'magic_shield', 'sword', 'magic_sword',
            'elixir', 'flash', 'log', 'can_play'
        ]

    def get_can_play(self, obj):
        try:
            return obj.status.can_play
        except PlayerStatus.DoesNotExist:
            return True
