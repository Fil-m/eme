from django.apps import AppConfig

class NetworkConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'network'
    verbose_name = 'EME Network'

    def ready(self):
        try:
            from .discovery import discovery_service
            discovery_service.start()
        except Exception as e:
            print(f"Discovery start failed: {e}")
