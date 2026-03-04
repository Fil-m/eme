from django.contrib import admin
from .models import Node, ChatRoom, Message


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'ip_address', 'is_active', 'created_at']
    list_filter = ['is_active']


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['title', 'room_type', 'created_at']
    list_filter = ['room_type']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'room', 'text', 'is_read', 'created_at']
    list_filter = ['is_read']
