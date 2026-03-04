from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, MeView, SocialLinkCreateView, SocialLinkDestroyView,
    UserListView, UserDetailView, ChangePasswordView, AvatarUploadView,
    LogoutView, FollowView, UnfollowView, FollowersListView, FollowingListView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('me/avatar/', AvatarUploadView.as_view(), name='avatar-upload'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('social-links/', SocialLinkCreateView.as_view(), name='social-link-create'),
    path('social-links/<int:pk>/', SocialLinkDestroyView.as_view(), name='social-link-delete'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/follow/', FollowView.as_view(), name='follow'),
    path('users/<int:pk>/unfollow/', UnfollowView.as_view(), name='unfollow'),
    path('users/<int:pk>/followers/', FollowersListView.as_view(), name='followers'),
    path('users/<int:pk>/following/', FollowingListView.as_view(), name='following'),
]
