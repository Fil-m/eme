from django.urls import path
from .views import CoreSettingsView

urlpatterns = [
    path('me/', CoreSettingsView.as_view(), name='core_settings_me'),
]
