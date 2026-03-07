from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CoreSettingsView, UserAppLayoutViewSet,
    AIDraftAppViewSet, AIAppGenerateView, AppPublishView
)

router = DefaultRouter()
router.register(r'apps', UserAppLayoutViewSet, basename='user-app-layouts')
router.register(r'ai-drafts', AIDraftAppViewSet, basename='ai-draft-app')

urlpatterns = [
    path('me/', CoreSettingsView.as_view(), name='core_settings_me'),
    path('ai-builder/generate/', AIAppGenerateView.as_view(), name='ai_app_generate'),
    path('ai-builder/publish/<int:pk>/', AppPublishView.as_view(), name='ai_app_publish'),
    path('', include(router.urls)),
]
