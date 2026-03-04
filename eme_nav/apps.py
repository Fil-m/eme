from django.apps import AppConfig


class EmeNavConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'eme_nav'
    verbose_name = 'EME Navigation'

    def ready(self):
        pass
