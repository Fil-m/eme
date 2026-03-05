from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import (ChatRoom, RoomMember, Message, StickerPack, Sticker,
                     ChatSettings, UserActiveStickerPack)
from .serializers import (ChatRoomSerializer, RoomMemberSerializer, MessageSerializer,
                          StickerPackSerializer, StickerSerializer, ChatSettingsSerializer)

User = get_user_model()


class ChatRoomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        user = self.request.user
        # User sees: general rooms + rooms they're a member of
        return ChatRoom.objects.filter(
            Q(kind='general') | Q(members__user=user)
        ).distinct()

    def perform_create(self, serializer):
        room = serializer.save(creator=self.request.user)
        # Creator is automatically owner
        RoomMember.objects.create(room=room, user=self.request.user, role=RoomMember.Role.OWNER)

    @action(detail=False, methods=['post'])
    def direct(self, request):
        """Get or create a DM between current user and another user"""
        target_id = request.data.get('user_id')
        if not target_id:
            return Response({'error': 'user_id required'}, status=400)
        
        try:
            target = User.objects.get(id=target_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        # Find existing DM between these two users
        existing = ChatRoom.objects.filter(kind='dm', members__user=request.user).filter(
            members__user=target
        ).first()

        if existing:
            return Response(ChatRoomSerializer(existing, context={'request': request}).data)

        room = ChatRoom.objects.create(kind='dm', title='', creator=request.user)
        RoomMember.objects.create(room=room, user=request.user, role=RoomMember.Role.OWNER)
        RoomMember.objects.create(room=room, user=target, role=RoomMember.Role.MEMBER)

        return Response(ChatRoomSerializer(room, context={'request': request}).data, status=201)

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        room = self.get_object()
        members = room.members.all()
        return Response(RoomMemberSerializer(members, many=True).data)

    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        room = self.get_object()
        # Only owner/admin can invite
        my_membership = room.members.filter(user=request.user).first()
        if not my_membership or my_membership.role not in ['owner', 'admin']:
            return Response({'error': 'Permission denied'}, status=403)

        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        member, created = RoomMember.objects.get_or_create(
            room=room, user=user, defaults={'role': RoomMember.Role.MEMBER}
        )
        return Response(RoomMemberSerializer(member).data, status=201 if created else 200)

    @action(detail=True, methods=['post'], url_path='members/(?P<user_id>[^/.]+)/role')
    def set_role(self, request, pk=None, user_id=None):
        room = self.get_object()
        my_membership = room.members.filter(user=request.user).first()
        if not my_membership or my_membership.role != 'owner':
            return Response({'error': 'Only owner can change roles'}, status=403)
        
        new_role = request.data.get('role')
        if new_role not in ['admin', 'member']:
            return Response({'error': 'Invalid role'}, status=400)

        member = room.members.filter(user_id=user_id).first()
        if not member:
            return Response({'error': 'Member not found'}, status=404)
        
        member.role = new_role
        member.save()
        return Response(RoomMemberSerializer(member).data)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        room = self.get_object()
        room.members.filter(user=request.user).delete()
        return Response(status=204)


class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        room_id = self.kwargs.get('room_pk')
        # Ensure user is a member or it's general
        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return Message.objects.none()

        if room.kind != 'general' and not room.members.filter(user=self.request.user).exists():
            return Message.objects.none()

        return Message.objects.filter(room_id=room_id)

    def perform_create(self, serializer):
        room_id = self.kwargs.get('room_pk')
        room = ChatRoom.objects.get(id=room_id)
        serializer.save(sender=self.request.user, room=room)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class StickerPackViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StickerPackSerializer

    def get_queryset(self):
        if self.action == 'public':
            return StickerPack.objects.filter(is_public=True)
        return StickerPack.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'])
    def public(self, request):
        packs = StickerPack.objects.filter(is_public=True)
        return Response(StickerPackSerializer(packs, many=True).data)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        pack = self.get_object()
        if pack.owner != request.user:
            return Response({'error': 'Not your pack'}, status=403)
        pack.is_public = not pack.is_public
        pack.save()
        return Response({'is_public': pack.is_public})

    @action(detail=True, methods=['post'])
    def add_sticker(self, request, pk=None):
        pack = self.get_object()
        if pack.owner != request.user:
            return Response({'error': 'Not your pack'}, status=403)
        
        serializer = StickerSerializer(data={
            'pack': pack.id,
            'image': request.data.get('image'),
            'label': request.data.get('label', ''),
        })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get user's activated packs (own + subscribed public)"""
        own_packs = StickerPack.objects.filter(owner=request.user)
        activated_ids = UserActiveStickerPack.objects.filter(
            user=request.user).values_list('pack_id', flat=True)
        public_packs = StickerPack.objects.filter(id__in=activated_ids, is_public=True)
        packs = (own_packs | public_packs).distinct()
        return Response(StickerPackSerializer(packs, many=True).data)

    @action(detail=True, methods=['post'], url_path='activate')
    def activate_pack(self, request, pk=None):
        pack = self.get_object()
        if not pack.is_public and pack.owner != request.user:
            return Response({'error': 'Pack not accessible'}, status=403)
        UserActiveStickerPack.objects.get_or_create(user=request.user, pack=pack)
        return Response({'activated': True})

    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate_pack(self, request, pk=None):
        pack = self.get_object()
        UserActiveStickerPack.objects.filter(user=request.user, pack=pack).delete()
        return Response({'activated': False})


class ChatSettingsView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        settings_obj, _ = ChatSettings.objects.get_or_create(user=request.user)
        return Response(ChatSettingsSerializer(settings_obj).data)

    def create(self, request):
        settings_obj, _ = ChatSettings.objects.get_or_create(user=request.user)
        serializer = ChatSettingsSerializer(settings_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
