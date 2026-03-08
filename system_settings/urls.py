from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CoreSettingsView, UserAppLayoutViewSet,
    AIDraftAppViewSet, AIAppGenerateView, AppPublishView,
    AppListView, AppPreviewView, AppDeleteView,
    AppGitPushView, GitAutoUpdateView
)

router = DefaultRouter()
router.register(r'apps', UserAppLayoutViewSet, basename='user-app-layouts')
router.register(r'ai-drafts', AIDraftAppViewSet, basename='ai-draft-app')

urlpatterns = [
    path('me/', CoreSettingsView.as_view(), name='core_settings_me'),
    path('ai-builder/generate/', AIAppGenerateView.as_view(), name='ai_app_generate'),
    path('ai-builder/publish/<int:pk>/', AppPublishView.as_view(), name='ai_app_publish'),
    path('ai-builder/delete/<int:pk>/', AppDeleteView.as_view(), name='ai_app_delete'),
    path('ai-builder/push/<int:pk>/', AppGitPushView.as_view(), name='ai_app_push'),
    path('git/sync/', GitAutoUpdateView.as_view(), name='git_sync'),
    path('ai-builder/preview/', AppPreviewView.as_view(), name='ai_app_preview'),
    path('available-apps/', AppListView.as_view(), name='available_apps'),
    path('', include(router.urls)),
]
