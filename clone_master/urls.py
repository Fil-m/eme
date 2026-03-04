from django.urls import path
from .views import ModuleListView, CloneCreateView, IPDiscoveryView

urlpatterns = [
    path('modules/', ModuleListView.as_view(), name='module-list'),
    path('create/', CloneCreateView.as_view(), name='clone-create'),
    path('ip/', IPDiscoveryView.as_view(), name='ip-discovery'),
]
