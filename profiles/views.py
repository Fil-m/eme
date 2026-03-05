from rest_framework import generics, permissions, status, parsers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from .models import EMEUser, SocialLink, FollowRelation, WallPost, WallComment
from .serializers import (
    EMEUserSerializer, RegisterSerializer, SocialLinkSerializer,
    ChangePasswordSerializer, WallPostSerializer, WallCommentSerializer
)


class RegisterView(generics.CreateAPIView):
    queryset = EMEUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': EMEUserSerializer(user, context={'request': request}).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = EMEUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AvatarUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def patch(self, request):
        user = request.user
        avatar = request.FILES.get('avatar')
        if not avatar:
            return Response({'error': 'Файл не надано'}, status=status.HTTP_400_BAD_REQUEST)
        user.avatar = avatar
        user.save(update_fields=['avatar'])
        return Response({'avatar': request.build_absolute_uri(user.avatar.url)})


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Пароль змінено'})


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Вийшли успішно'})
        except Exception:
            return Response({'error': 'Невалідний токен'}, status=status.HTTP_400_BAD_REQUEST)


class SocialLinkCreateView(generics.CreateAPIView):
    serializer_class = SocialLinkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SocialLinkDestroyView(generics.DestroyAPIView):
    queryset = SocialLink.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SocialLink.objects.filter(user=self.request.user)


class UserListView(generics.ListAPIView):
    queryset = EMEUser.objects.all().order_by('-last_seen')
    serializer_class = EMEUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'bio']
    ordering_fields = ['username', 'points', 'level', 'last_seen']


class UserDetailView(generics.RetrieveAPIView):
    queryset = EMEUser.objects.all()
    serializer_class = EMEUserSerializer
    permission_classes = [permissions.IsAuthenticated]


class FollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        target = get_object_or_404(EMEUser, pk=pk)
        if target == request.user:
            return Response({'error': 'Не можна підписатись на себе'}, status=status.HTTP_400_BAD_REQUEST)
        _, created = FollowRelation.objects.get_or_create(
            follower=request.user, following=target
        )
        if created:
            request.user.award_points(5, 'follow')
        return Response({'status': 'followed', 'created': created})


class UnfollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        target = get_object_or_404(EMEUser, pk=pk)
        FollowRelation.objects.filter(follower=request.user, following=target).delete()
        return Response({'status': 'unfollowed'})


class FollowersListView(generics.ListAPIView):
    serializer_class = EMEUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = get_object_or_404(EMEUser, pk=self.kwargs['pk'])
        follower_ids = user.followers.values_list('follower_id', flat=True)
        return EMEUser.objects.filter(id__in=follower_ids)


class FollowingListView(generics.ListAPIView):
    serializer_class = EMEUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = get_object_or_404(EMEUser, pk=self.kwargs['pk'])
        following_ids = user.following.values_list('following_id', flat=True)
        return EMEUser.objects.filter(id__in=following_ids)


class WallPostViewSet(viewsets.ModelViewSet):
    queryset = WallPost.objects.all()
    serializer_class = WallPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        owner_id = self.request.query_params.get('owner')
        if owner_id:
            return WallPost.objects.filter(owner_id=owner_id)
        return WallPost.objects.all()

    def perform_create(self, serializer):
        owner_id = self.request.data.get('owner')
        if owner_id:
            serializer.save(author=self.request.user, owner_id=owner_id)
        else:
            serializer.save(author=self.request.user, owner=self.request.user)


class WallCommentViewSet(viewsets.ModelViewSet):
    queryset = WallComment.objects.all()
    serializer_class = WallCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
