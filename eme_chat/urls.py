from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, MessageViewSet, StickerPackViewSet, ChatSettingsView

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='chatroom')
router.register(r'stickerpacks', StickerPackViewSet, basename='stickerpack')
router.register(r'settings', ChatSettingsView, basename='chatsettings')

# Manually wire nested messages endpoint to avoid drf-nested-routers
msg_list = MessageViewSet.as_view({'get': 'list', 'post': 'create'})
msg_detail = MessageViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})

urlpatterns = [
    path('', include(router.urls)),
    path('rooms/<uuid:room_pk>/messages/', msg_list, name='room-messages-list'),
    path('rooms/<uuid:room_pk>/messages/<uuid:pk>/', msg_detail, name='room-messages-detail'),
]
