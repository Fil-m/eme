from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MediaFileViewSet, CollectionViewSet, SharedFileView, ExplorerViewSet

router = DefaultRouter()
router.register(r'files', MediaFileViewSet, basename='mediafile')
router.register(r'collections', CollectionViewSet, basename='collection')
router.register(r'shared', SharedFileView, basename='shared')
router.register(r'explorer', ExplorerViewSet, basename='explorer')

urlpatterns = [
    path('', include(router.urls)),
]
