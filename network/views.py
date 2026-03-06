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

        ip = request.META.get('REMOTE_ADDR', '')
        node, created = Node.objects.update_or_create(
            user=user,
            defaults={
                'name': f'{user.username}-node',
                'device_id': str(uuid.uuid4()) if not getattr(user, 'node', None) else user.node.device_id,
                'ip_address': ip,
                'is_active': True,
            }
        )
        
        # Also register in discovery service known peers
        from .discovery import discovery_service
        if discovery_service and ip and ip != '127.0.0.1':
            discovery_service.known_peers.add(ip)

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

    def _register_node(self, request):
        """Helper to register/update node info from request IP."""
        from network.models import Node
        ip = request.META.get('REMOTE_ADDR')
        if not ip or ip == '127.0.0.1':
            return
        
        # Simple extraction of node name if provided in headers or params
        node_name = request.query_params.get('node_name', 'Remote Node')
        
        Node.objects.update_or_create(
            ip_address=ip,
            user=request.user,
            defaults={'name': node_name, 'is_active': True}
        )
        # Also let discovery service know
        from network.discovery import discovery_service
        if discovery_service:
            discovery_service.known_peers.add(ip)

    def get(self, request):
        self._register_node(request)
        from profiles.models import WallPost, WallComment, EMEUser
        from eme_chat.models import Message
        from eme_media.models import Collection, MediaFile
        from projects.models import Project, ProjectRole, ProjectMember, ProjectAction
        
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
        elif obj_type == 'user':
            u = EMEUser.objects.filter(username=sync_id).first()
            if u:
                data = {
                    'username': u.username,
                    'first_name': u.first_name,
                    'last_name': u.last_name,
                    'bio': u.bio,
                    'level': u.level,
                    'points': u.points,
                }
        elif obj_type == 'collection':
            col = Collection.objects.filter(sync_id=sync_id).first()
            if col:
                data = {
                    'sync_id': str(col.sync_id),
                    'user_username': col.user.username,
                    'name': col.name,
                    'description': col.description,
                    'parent_sync_id': str(col.parent.sync_id) if col.parent else None,
                    'created_at': col.created_at.isoformat()
                }
        elif obj_type == 'mediafile':
            mf = MediaFile.objects.filter(sync_id=sync_id).first()
            if mf:
                data = {
                    'sync_id': str(mf.sync_id),
                    'user_username': mf.user.username,
                    'collection_sync_id': str(mf.collection.sync_id) if mf.collection else None,
                    'file_name': mf.file_name,
                    'file_size': mf.file_size,
                    'mime_type': mf.mime_type,
                    'visibility': mf.visibility,
                    'created_at': mf.created_at.isoformat(),
                    'file_url': mf.file.url if mf.file else None,
                }
        elif obj_type == 'project':
            proj = Project.objects.filter(sync_id=sync_id).first()
            if proj:
                data = {
                    'sync_id': str(proj.sync_id),
                    'owner_username': proj.owner.username,
                    'title': proj.title,
                    'description': proj.description,
                    'emoji': proj.emoji,
                    'domain': proj.domain,
                    'status': proj.status,
                    'priority': proj.priority,
                    'deadline': proj.deadline.isoformat() if proj.deadline else None,
                    'next_action': proj.next_action,
                    'is_public': proj.is_public,
                    'order': proj.order,
                    'created_at': proj.created_at.isoformat(),
                    'updated_at': proj.updated_at.isoformat()
                }
        elif obj_type == 'projectrole':
            pr = ProjectRole.objects.filter(sync_id=sync_id).first()
            if pr:
                data = {
                    'sync_id': str(pr.sync_id),
                    'project_sync_id': str(pr.project.sync_id),
                    'name': pr.name,
                    'emoji': pr.emoji,
                    'description': pr.description,
                    'created_at': pr.created_at.isoformat()
                }
        elif obj_type == 'projectmember':
            pm = ProjectMember.objects.filter(sync_id=sync_id).first()
            if pm:
                data = {
                    'sync_id': str(pm.sync_id),
                    'project_sync_id': str(pm.project.sync_id),
                    'user_username': pm.user.username,
                    'role_sync_id': str(pm.role.sync_id) if pm.role else None,
                    'joined_at': pm.joined_at.isoformat()
                }
        elif obj_type == 'chatroom':
            from eme_chat.models import ChatRoom
            room = ChatRoom.objects.filter(id=sync_id).first()
            if room:
                data = {
                    'id': str(room.id),
                    'kind': room.kind,
                    'title': room.title,
                    'creator_username': room.creator.username if room.creator else None,
                    'description': room.description,
                    'created_at': room.created_at.isoformat()
                }
        elif obj_type == 'roommember':
            from eme_chat.models import RoomMember
            member = RoomMember.objects.filter(sync_id=sync_id).first()
            if member:
                data = {
                    'sync_id': str(member.sync_id),
                    'room_id': str(member.room.id),
                    'user_username': member.user.username,
                    'role': member.role,
                    'joined_at': member.joined_at.isoformat()
                }
        elif obj_type == 'projectaction':
            pa = ProjectAction.objects.filter(sync_id=sync_id).first()
            if pa:
                data = {
                    'sync_id': str(pa.sync_id),
                    'project_sync_id': str(pa.project.sync_id),
                    'text': pa.text,
                    'status': pa.status,
                    'is_done': pa.is_done,
                    'priority': pa.priority,
                    'deadline': pa.deadline.isoformat() if pa.deadline else None,
                    'due_date': pa.due_date.isoformat() if pa.due_date else None,
                    'depends_on_sync_id': str(pa.depends_on.sync_id) if pa.depends_on else None,
                    'assignee_sync_id': str(pa.assignee.sync_id) if pa.assignee else None,
                    'assignee_role_sync_id': str(pa.assignee_role.sync_id) if pa.assignee_role else None,
                    'created_at': pa.created_at.isoformat()
                }

        if not data:
            return Response({"error": "Not found"}, status=404)
            
        return Response(data)

class SyncCatchupView(APIView):
    """Download all missed objects since a specific timestamp."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Auto-register node from IP
        from network.models import Node
        ip = request.META.get('REMOTE_ADDR')
        if ip and ip != '127.0.0.1':
            Node.objects.update_or_create(
                ip_address=ip,
                user=request.user,
                defaults={'is_active': True}
            )
            from network.discovery import discovery_service
            if discovery_service:
                discovery_service.known_peers.add(ip)

        from profiles.models import WallPost, WallComment, EMEUser
        from eme_chat.models import Message
        from eme_media.models import Collection, MediaFile
        from projects.models import Project, ProjectRole, ProjectMember, ProjectAction
        from datetime import datetime, timezone
        from django.utils import timezone as django_timezone
        
        since_ts = float(request.query_params.get('since', 0))
        # Use timezone.utc as the baseline for sync timestamps
        since_dt = datetime.fromtimestamp(since_ts, tz=timezone.utc)
        items = []
        
        # Users
        for u in EMEUser.objects.filter(date_joined__gt=since_dt):
            items.append({
                'type': 'user',
                'data': {
                    'username': u.username,
                    'first_name': u.first_name,
                    'last_name': u.last_name,
                    'bio': u.bio,
                    'level': u.level,
                    'points': u.points,
                }
            })

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

        # ChatRooms
        from eme_chat.models import ChatRoom, RoomMember
        for room in ChatRoom.objects.filter(created_at__gt=since_dt):
            items.append({
                'type': 'chatroom',
                'data': {
                    'id': str(room.id),
                    'kind': room.kind,
                    'title': room.title,
                    'creator_username': room.creator.username if room.creator else None,
                    'description': room.description,
                    'created_at': room.created_at.isoformat()
                }
            })
            
        # RoomMembers
        for member in RoomMember.objects.filter(joined_at__gt=since_dt):
            items.append({
                'type': 'roommember',
                'data': {
                    'sync_id': str(member.sync_id),
                    'room_id': str(member.room.id),
                    'user_username': member.user.username,
                    'role': member.role,
                    'joined_at': member.joined_at.isoformat()
                }
            })

        # Collections
        for col in Collection.objects.filter(created_at__gt=since_dt):
            items.append({
                'type': 'collection',
                'data': {
                    'sync_id': str(col.sync_id),
                    'user_username': col.user.username,
                    'name': col.name,
                    'description': col.description,
                    'parent_sync_id': str(col.parent.sync_id) if col.parent else None,
                    'created_at': col.created_at.isoformat()
                }
            })

        # MediaFiles
        for mf in MediaFile.objects.filter(created_at__gt=since_dt):
            items.append({
                'type': 'mediafile',
                'data': {
                    'sync_id': str(mf.sync_id),
                    'user_username': mf.user.username,
                    'collection_sync_id': str(mf.collection.sync_id) if mf.collection else None,
                    'file_name': mf.file_name,
                    'file_size': mf.file_size,
                    'mime_type': mf.mime_type,
                    'visibility': mf.visibility,
                    'created_at': mf.created_at.isoformat(),
                    'file_url': mf.file.url if mf.file else None,
                }
            })

        # Projects
        for proj in Project.objects.filter(updated_at__gt=since_dt):
            items.append({
                'type': 'project',
                'data': {
                    'sync_id': str(proj.sync_id),
                    'owner_username': proj.owner.username,
                    'title': proj.title,
                    'description': proj.description,
                    'emoji': proj.emoji,
                    'domain': proj.domain,
                    'status': proj.status,
                    'priority': proj.priority,
                    'deadline': proj.deadline.isoformat() if proj.deadline else None,
                    'next_action': proj.next_action,
                    'is_public': proj.is_public,
                    'order': proj.order,
                    'created_at': proj.created_at.isoformat(),
                    'updated_at': proj.updated_at.isoformat()
                }
            })

        # ProjectRoles
        for pr in ProjectRole.objects.filter(created_at__gt=since_dt):
            items.append({
                'type': 'projectrole',
                'data': {
                    'sync_id': str(pr.sync_id),
                    'project_sync_id': str(pr.project.sync_id),
                    'name': pr.name,
                    'emoji': pr.emoji,
                    'description': pr.description,
                    'created_at': pr.created_at.isoformat()
                }
            })

        # ProjectMembers
        for pm in ProjectMember.objects.filter(joined_at__gt=since_dt):
            items.append({
                'type': 'projectmember',
                'data': {
                    'sync_id': str(pm.sync_id),
                    'project_sync_id': str(pm.project.sync_id),
                    'user_username': pm.user.username,
                    'role_sync_id': str(pm.role.sync_id) if pm.role else None,
                    'joined_at': pm.joined_at.isoformat()
                }
            })

        # ProjectActions
        for pa in ProjectAction.objects.filter(created_at__gt=since_dt):
            items.append({
                'type': 'projectaction',
                'data': {
                    'sync_id': str(pa.sync_id),
                    'project_sync_id': str(pa.project.sync_id),
                    'text': pa.text,
                    'status': pa.status,
                    'is_done': pa.is_done,
                    'priority': pa.priority,
                    'deadline': pa.deadline.isoformat() if pa.deadline else None,
                    'due_date': pa.due_date.isoformat() if pa.due_date else None,
                    'depends_on_sync_id': str(pa.depends_on.sync_id) if pa.depends_on else None,
                    'assignee_sync_id': str(pa.assignee.sync_id) if pa.assignee else None,
                    'assignee_role_sync_id': str(pa.assignee_role.sync_id) if pa.assignee_role else None,
                    'created_at': pa.created_at.isoformat()
                }
            })

        return Response({"items": items})
