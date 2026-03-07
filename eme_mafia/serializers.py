from rest_framework import serializers
from .models import GameRoom, Player, GameAction, ChatMessage


class PlayerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    avatar_url = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = Player
        fields = ['id', 'user', 'username', 'avatar_url', 'role', 'role_display', 'is_alive', 'joined_at']
        read_only_fields = ['id', 'joined_at', 'role'] # Role represents internal state, usually assigned by engine

    def get_avatar_url(self, obj):
        u = obj.user
        if hasattr(u, 'avatar') and u.avatar:
            return u.avatar.url
        return None

class GameRoomSerializer(serializers.ModelSerializer):
    players = PlayerSerializer(many=True, read_only=True)
    host_username = serializers.CharField(source='host.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    players_count = serializers.SerializerMethodField()

    class Meta:
        model = GameRoom
        fields = [
            'id', 'name', 'host', 'host_username', 'status', 'status_display',
            'human_moderator', 'phase_number', 'phase_deadline', 
            'players', 'players_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'host', 'status', 'phase_number', 'phase_deadline', 'created_at', 'updated_at']

    def get_players_count(self, obj):
        return obj.players.count()


class GameActionSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.user.username', read_only=True)
    target_name = serializers.SerializerMethodField()
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)

    class Meta:
        model = GameAction
        fields = ['id', 'actor', 'actor_name', 'target', 'target_name', 'action_type', 'action_type_display', 'phase_number', 'is_night_action', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_target_name(self, obj):
        if obj.target:
            return obj.target.user.username
        return None


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'room', 'sender', 'sender_name', 'text', 'msg_type', 'created_at']
        read_only_fields = ['id', 'created_at', 'room']

    def get_sender_name(self, obj):
        if obj.sender:
            return obj.sender.user.username
        return "System"
