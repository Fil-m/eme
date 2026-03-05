from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.PlayerStatusView.as_view(), name='game-status'),
    path('action/', views.PlayerActionView.as_view(), name='game-action'),
    path('qr/', views.QRCodeProcessView.as_view(), name='game-qr'),
    path('admin/players/', views.PlayerAdminView.as_view(), name='game-admin'),
]
