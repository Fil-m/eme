from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatRoom, RoomMember, Message, StickerPack, Sticker, ChatSettings, UserActiveStickerPack

User = get_user_model()


class MiniUserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'avatar']

    def get_avatar(self, obj):
        try:
            return obj.profile.avatar.url if obj.profile.avatar else None
        except Exception:
            return None


class RoomMemberSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer(read_only=True)

    class Meta:
        model = RoomMember
        fields = ['id', 'user', 'role', 'is_muted', 'joined_at']


class ChatRoomSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    my_role = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'kind', 'title', 'description', 'avatar_url', 'creator',
                  'members_count', 'last_message', 'my_role', 'unread_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at',
                            'members_count', 'last_message', 'my_role', 'avatar_url', 'unread_count']

    def get_members_count(self, obj):
        return obj.members.count()

    def get_last_message(self, obj):
        msg = obj.messages.last()
        if msg:
            return {
                'text': msg.text[:60] if msg.text else f"[{msg.msg_type}]",
                'sender': msg.sender.username,
                'created_at': msg.created_at.isoformat()
            }
        return None

    def get_my_role(self, obj):
        request = self.context.get('request')
        if request:
            m = obj.members.filter(user=request.user).first()
            return m.role if m else None
        return None

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None

    def get_unread_count(self, obj):
        # Simple: return 0 for now; can be enhanced with read tracking
        return 0


class StickerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Sticker
        fields = ['id', 'pack', 'image', 'image_url', 'label', 'order']
        read_only_fields = ['id']

    def get_image_url(self, obj):
        try:
            return obj.image.url
        except Exception:
            return None


class StickerPackSerializer(serializers.ModelSerializer):
    stickers = StickerSerializer(many=True, read_only=True)
    stickers_count = serializers.SerializerMethodField()

    class Meta:
        model = StickerPack
        fields = ['id', 'name', 'owner', 'is_public', 'stickers_count', 'stickers', 'created_at']
        read_only_fields = ['id', 'owner', 'stickers', 'stickers_count', 'created_at']

    def get_stickers_count(self, obj):
        return obj.stickers.count()


class MessageSerializer(serializers.ModelSerializer):
    sender_info = MiniUserSerializer(source='sender', read_only=True)
    sticker_data = StickerSerializer(source='sticker', read_only=True)
    attachment_url = serializers.SerializerMethodField()
    attachment_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'room', 'sender', 'sender_info', 'msg_type', 'text',
                  'sticker', 'sticker_data', 'attachment', 'attachment_url', 'attachment_name', 'created_at']
        read_only_fields = ['id', 'room', 'sender', 'sender_info', 'sticker_data',
                            'attachment_url', 'attachment_name', 'created_at']

    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get('request')
            try:
                url = obj.attachment.file.url
                return request.build_absolute_uri(url) if request else url
            except Exception:
                return None
        return None

    def get_attachment_name(self, obj):
        if obj.attachment:
            try:
                import os
                return os.path.basename(obj.attachment.file.name)
            except Exception:
                return None
        return None


class ChatSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSettings
        fields = ['stickers_enabled', 'pixel_editor_enabled']
