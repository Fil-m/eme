import socket
from rest_framework import serializers
from .models import CoreSettings, UserAppLayout, AIDraftApp


class CoreSettingsSerializer(serializers.ModelSerializer):
    server_ip = serializers.SerializerMethodField()
    published_modules = serializers.SerializerMethodField()

    class Meta:
        model = CoreSettings
        fields = [
            'id', 'node_name', 'theme', 'language', 'auto_update',
            'dock_apps',
            'notification_enabled', 'notification_chat', 'notification_mesh',
            'is_mesh_enabled', 'mesh_sync_interval', 'server_ip', 'published_modules'
        ]
        read_only_fields = ['id', 'server_ip', 'published_modules']

    def get_server_ip(self, obj):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
            
    def get_published_modules(self, obj):
        import re
        qs = AIDraftApp.objects.filter(is_published=True).order_by('created_at')
        modules = []
        for app in qs:
            base_id = app.component_name.lower().replace("eme", "")
            if not base_id:
                base_id = f"custom_{app.id}"
                
            # JS logic replica: name.replace(/[A-Z]/g, m => "-" + m.toLowerCase()).replace(/^-/, "");
            kebab_comp = re.sub(r'[A-Z]', lambda m: '-' + m.group(0).lower(), app.component_name)
            if kebab_comp.startswith('-'):
                kebab_comp = kebab_comp[1:]
                
            modules.append({
                "id": base_id,
                "label": app.name,
                "icon": "🤖",
                "comp": kebab_comp
            })
        return modules


class UserAppLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAppLayout
        fields = ['id', 'name', 'icon', 'modules', 'created_at']
        read_only_fields = ['id', 'created_at']

class AIDraftAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIDraftApp
        fields = ['id', 'name', 'description', 'component_name', 'vue_code', 'is_published', 'created_at']
        read_only_fields = ['id', 'is_published', 'created_at']

