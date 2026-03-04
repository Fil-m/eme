from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NavItemViewSet

router = DefaultRouter()
router.register(r'items', NavItemViewSet, basename='navitem')

urlpatterns = [
    path('', include(router.urls)),
]
