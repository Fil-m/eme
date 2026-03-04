from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HeartbeatView, MeshDiscoveryView, DirectMessageView,
    ChatRoomViewSet, MessageViewSet, SyncPullView, SyncPushView,
)

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='chatroom')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('heartbeat/', HeartbeatView.as_view(), name='heartbeat'),
    path('discovery/', MeshDiscoveryView.as_view(), name='mesh-discovery'),
    path('dm/', DirectMessageView.as_view(), name='direct-message'),
    path('sync/pull/', SyncPullView.as_view(), name='sync-pull'),
    path('sync/push/', SyncPushView.as_view(), name='sync-push'),
    path('', include(router.urls)),
]
