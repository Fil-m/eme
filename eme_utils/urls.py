from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookmarkViewSet, PastebinSnippetViewSet, MemoViewSet, SysMonView

router = DefaultRouter()
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')
router.register(r'pastebin', PastebinSnippetViewSet, basename='pastebin')
router.register(r'memos', MemoViewSet, basename='memo')

urlpatterns = [
    path('sysmon/', SysMonView.as_view(), name='sysmon'),
    path('', include(router.urls)),
]
