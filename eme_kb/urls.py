from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KBCategoryViewSet, KBArticleViewSet

router = DefaultRouter()
router.register(r'categories', KBCategoryViewSet, basename='kbcategory')
router.register(r'articles', KBArticleViewSet, basename='kbarticle')

urlpatterns = [
    path('', include(router.urls)),
]
