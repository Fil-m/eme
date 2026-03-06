from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404
import uuid
from .models import Node, ChatRoom, Message
from .serializers import NodeSerializer, ChatRoomSerializer, MessageSerializer


class HeartbeatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.last_seen = timezone.now()
        user.save(update_fields=['last_seen'])

        node, created = Node.objects.get_or_create(
            user=user,
            defaults={
                'name': f'{user.username}-node',
                'device_id': str(uuid.uuid4()),
                'ip_address': request.META.get('REMOTE_ADDR', ''),
            }
        )
        if not created:
            node.is_active = True
            node.ip_address = request.META.get('REMOTE_ADDR', '')
            node.save(update_fields=['is_active', 'ip_address'])

        return Response({
            'status': 'ok',
            'node': node.name,
            'ts': timezone.now(),
        })


class MeshDiscoveryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from profiles.models import EMEUser
        from .discovery import discovery_service
        
        users = EMEUser.objects.all().order_by('-last_seen')[:50]
        nodes = Node.objects.filter(is_active=True)
        external_nodes = discovery_service.get_active_nodes()

        user_data = []
        for u in users:
            user_data.append({
                'id': u.id,
                'username': u.username,
                'first_name': u.first_name,
                'points': u.points,
                'level': u.level,
                'is_online': u.last_seen and u.last_seen > timezone.now() - timezone.timedelta(minutes=5),
                'avatar': u.avatar.url if u.avatar else None,
            })

        node_data = NodeSerializer(nodes, many=True).data

        return Response({
            'users': user_data,
            'nodes': node_data,
            'external_nodes': external_nodes,
            'total_nodes': nodes.count() + len(external_nodes),
        })


class DirectMessageView(APIView):
    """Get or create a DM room between current user and target user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from profiles.models import EMEUser
        target_id = request.data.get('user_id')
        if not target_id:
            return Response({'error': 'user_id обов\'язковий'}, status=status.HTTP_400_BAD_REQUEST)

        target = get_object_or_404(EMEUser, pk=target_id)
        if target == request.user:
            return Response({'error': 'Не можна створити DM з собою'}, status=status.HTTP_400_BAD_REQUEST)

        # Find existing DM room between these two users
        dm_rooms = ChatRoom.objects.filter(
            room_type='dm',
            participants=request.user,
        ).filter(
            participants=target,
        )

        if dm_rooms.exists():
            room = dm_rooms.first()
        else:
            room = ChatRoom.objects.create(
                room_type='dm',
                title=f'{request.user.username} ↔ {target.username}'
            )
            room.participants.add(request.user, target)

        return Response(ChatRoomSerializer(room, context={'request': request}).data)


class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatRoom.objects.filter(participants=self.request.user).distinct()

    def perform_create(self, serializer):
        room = serializer.save()
        room.participants.add(self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Message.objects.filter(room__participants=self.request.user)
        room_id = self.request.query_params.get('room')
        if room_id:
            qs = qs.filter(room_id=room_id)
        return qs.distinct()

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['patch'], url_path='read')
    def mark_read(self, request, pk=None):
        message = self.get_object()
        message.is_read = True
        message.save(update_fields=['is_read'])
        return Response({'is_read': True})

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        room_id = request.data.get('room_id')
        if not room_id:
            return Response({'error': 'room_id обов\'язковий'}, status=status.HTTP_400_BAD_REQUEST)
        updated = Message.objects.filter(
            room_id=room_id, is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        return Response({'marked_read': updated})


class SyncPullView(APIView):
    """Download specific object data from this node for P2P sync."""
    permission_classes = [permissions.AllowAny] # Local mesh traffic

    def get(self, request):
        from profiles.models import WallPost, WallComment
        from eme_chat.models import Message
        
        obj_type = request.query_params.get('type')
        sync_id = request.query_params.get('sync_id')
        
        if not obj_type or not sync_id:
            return Response({"error": "Missing params"}, status=400)
            
        data = {}
        if obj_type == 'wallpost':
            post = WallPost.objects.filter(sync_id=sync_id).first()
            if post:
                data = {
                    'sync_id': str(post.sync_id),
                    'owner_username': post.owner.username,
                    'author_username': post.author.username,
                    'content': post.content,
                    'created_at': post.created_at.isoformat(),
                    'likes_count': post.likes_count
                }
        elif obj_type == 'wallcomment':
            comment = WallComment.objects.filter(sync_id=sync_id).first()
            if comment:
                data = {
                    'sync_id': str(comment.sync_id),
                    'post_sync_id': str(comment.post.sync_id),
                    'author_username': comment.author.username,
                    'content': comment.content,
                    'created_at': comment.created_at.isoformat()
                }
        elif obj_type == 'chatmessage':
            msg = Message.objects.filter(id=sync_id).first()
            if msg:
                data = {
                    'id': str(msg.id),
                    'room_id': str(msg.room.id),
                    'sender_username': msg.sender.username,
                    'text': msg.text,
                    'is_read': msg.is_read,
                    'created_at': msg.created_at.isoformat()
                }
                
        if not data:
            return Response({"error": "Not found"}, status=404)
            
        return Response(data)

class SyncCatchupView(APIView):
    """Download all missed objects since a specific timestamp."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from profiles.models import WallPost, WallComment
        from eme_chat.models import Message
        from datetime import datetime
        
        since_ts = float(request.query_params.get('since', 0))
        since_dt = datetime.fromtimestamp(since_ts)
        items = []
        
        # WallPosts
        for post in WallPost.objects.filter(created_at__gt=since_dt):
            items.append({
                'type': 'wallpost',
                'data': {
                    'sync_id': str(post.sync_id),
                    'owner_username': post.owner.username,
                    'author_username': post.author.username,
                    'content': post.content,
                    'created_at': post.created_at.isoformat(),
                    'likes_count': post.likes_count
                }
            })
            
        # WallComments
        for comment in WallComment.objects.filter(created_at__gt=since_dt):
            items.append({
                'type': 'wallcomment',
                'data': {
                    'sync_id': str(comment.sync_id),
                    'post_sync_id': str(comment.post.sync_id),
                    'author_username': comment.author.username,
                    'content': comment.content,
                    'created_at': comment.created_at.isoformat()
                }
            })
            
        # Messages
        for msg in Message.objects.filter(created_at__gt=since_dt):
            items.append({
                'type': 'chatmessage',
                'data': {
                    'id': str(msg.id),
                    'room_id': str(msg.room.id),
                    'sender_username': msg.sender.username,
                    'text': msg.text,
                    'is_read': msg.is_read,
                    'created_at': msg.created_at.isoformat()
                }
            })
            
        return Response({"items": items})
