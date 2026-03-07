from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GameRoomViewSet, PlayerViewSet, ChatMessageViewSet

router = DefaultRouter()
router.register(r'rooms', GameRoomViewSet, basename='gameroom')
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'messages', ChatMessageViewSet, basename='chatmessage')

urlpatterns = [
    path('', include(router.urls)),
]
