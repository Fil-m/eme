import socket
from rest_framework import serializers
from .models import CoreSettings


class CoreSettingsSerializer(serializers.ModelSerializer):
    server_ip = serializers.SerializerMethodField()

    class Meta:
        model = CoreSettings
        fields = [
            'id', 'node_name', 'theme', 'language', 'auto_update',
            'notification_enabled', 'notification_chat', 'notification_mesh',
            'is_mesh_enabled', 'mesh_sync_interval', 'server_ip',
        ]
        read_only_fields = ['id', 'server_ip']

    def get_server_ip(self, obj):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
