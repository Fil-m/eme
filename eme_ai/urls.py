from django.urls import path
from .views import ProviderListView, ScaffoldView, ScaffoldApplyView

urlpatterns = [
    path('providers/', ProviderListView.as_view(), name='ai-providers'),
    path('scaffold/', ScaffoldView.as_view(), name='ai-scaffold'),
    path('scaffold/apply/', ScaffoldApplyView.as_view(), name='ai-scaffold-apply'),
]
