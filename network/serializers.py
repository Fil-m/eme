from rest_framework import serializers
from .models import Node, ChatRoom, Message


class NodeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Node
        fields = [
            'id', 'user', 'username', 'name', 'device_id',
            'ip_address', 'is_active', 'last_sync_at', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'room', 'sender', 'sender_name', 'text',
            'attachment', 'is_read', 'created_at',
        ]
        read_only_fields = ['id', 'sender', 'created_at']


class ChatRoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    participant_names = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'title', 'room_type', 'participants',
            'participant_names', 'last_message', 'unread_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if msg:
            return {
                'text': msg.text[:100],
                'sender': msg.sender.username,
                'created_at': msg.created_at,
                'is_read': msg.is_read,
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0

    def get_participant_names(self, obj):
        return list(obj.participants.values_list('username', flat=True))
