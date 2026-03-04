from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import models
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.conf import settings as django_settings
import os
import mimetypes
from .models import MediaFile, Collection, Tag
from .serializers import MediaFileSerializer, CollectionSerializer, TagSerializer
from .utils import generate_preview


class CollectionViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        qs = Collection.objects.filter(user_id=user_id) if user_id else Collection.objects.filter(user=self.request.user)
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            qs = qs.filter(parent_id=parent_id)
        elif not self.kwargs.get('pk'):
            qs = qs.filter(parent__isnull=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'], url_path='rename')
    def rename(self, request, pk=None):
        collection = self.get_object()
        if collection.user != request.user:
            return Response({'error': 'Доступ заборонено'}, status=status.HTTP_403_FORBIDDEN)
        name = request.data.get('name')
        if not name:
            return Response({'error': 'Назва обов\'язкова'}, status=status.HTTP_400_BAD_REQUEST)
        collection.name = name
        collection.save(update_fields=['name'])
        return Response(CollectionSerializer(collection).data)


class MediaFileViewSet(viewsets.ModelViewSet):
    serializer_class = MediaFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['file_name', 'mime_type']
    ordering_fields = ['file_name', 'file_size', 'created_at']

    def get_queryset(self):
        user = self.request.user
        user_id = self.request.query_params.get('user_id')

        if user_id:
            from profiles.models import FollowRelation
            is_friend = FollowRelation.objects.filter(
                follower_id=user_id, following=user
            ).exists() and FollowRelation.objects.filter(
                follower=user, following_id=user_id
            ).exists()

            if is_friend:
                qs = MediaFile.objects.filter(
                    models.Q(user_id=user_id, visibility__in=['friends', 'public']) |
                    models.Q(user=user)
                )
            else:
                qs = MediaFile.objects.filter(
                    models.Q(user_id=user_id, visibility='public') |
                    models.Q(user=user)
                )
        else:
            qs = MediaFile.objects.filter(user=user)

        collection_id = self.request.query_params.get('collection')
        if collection_id:
            qs = qs.filter(collection_id=collection_id)

        mime_type = self.request.query_params.get('mime_type')
        if mime_type:
            qs = qs.filter(mime_type__startswith=mime_type)

        tag = self.request.query_params.get('tag')
        if tag:
            qs = qs.filter(tags__name=tag)

        return qs.distinct()

    def perform_create(self, serializer):
        file_obj = self.request.FILES.get('file')
        if file_obj:
            max_size = getattr(django_settings, 'MAX_UPLOAD_SIZE', 100 * 1024 * 1024)
            if file_obj.size > max_size:
                from rest_framework.exceptions import ValidationError
                raise ValidationError(f'Файл завеликий. Максимум: {max_size // (1024*1024)} MB')

            media_file = serializer.save(
                user=self.request.user,
                file_name=file_obj.name,
                file_size=file_obj.size,
                mime_type=file_obj.content_type or mimetypes.guess_type(file_obj.name)[0] or 'application/octet-stream'
            )
        else:
            media_file = serializer.save(user=self.request.user)

        generate_preview(media_file)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        media_file = get_object_or_404(MediaFile, pk=pk)

        if media_file.user != request.user and media_file.visibility == 'private':
            return Response({'error': 'Доступ заборонено'}, status=status.HTTP_403_FORBIDDEN)

        if media_file.file:
            response = FileResponse(media_file.file.open('rb'))
            target_name = media_file.file_name or os.path.basename(media_file.file.name)
        elif media_file.file_path and os.path.exists(media_file.file_path):
            response = FileResponse(open(media_file.file_path, 'rb'))
            target_name = media_file.file_name
        else:
            return Response({'error': 'Файл не знайдено'}, status=status.HTTP_404_NOT_FOUND)

        response['Content-Type'] = media_file.mime_type or 'application/octet-stream'
        response['Content-Disposition'] = f'attachment; filename="{target_name}"'
        return response

    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        """Inline preview without download (for images/video)."""
        media_file = get_object_or_404(MediaFile, pk=pk)

        if media_file.user != request.user and media_file.visibility == 'private':
            return Response({'error': 'Доступ заборонено'}, status=status.HTTP_403_FORBIDDEN)

        if media_file.file:
            response = FileResponse(media_file.file.open('rb'))
        elif media_file.file_path and os.path.exists(media_file.file_path):
            response = FileResponse(open(media_file.file_path, 'rb'))
        else:
            return Response({'error': 'Файл не знайдено'}, status=status.HTTP_404_NOT_FOUND)

        response['Content-Type'] = media_file.mime_type or 'application/octet-stream'
        response['Content-Disposition'] = f'inline; filename="{media_file.file_name}"'
        return response

    @action(detail=True, methods=['patch'])
    def rename(self, request, pk=None):
        media_file = self.get_object()
        if media_file.user != request.user:
            return Response({'error': 'Доступ заборонено'}, status=status.HTTP_403_FORBIDDEN)
        name = request.data.get('file_name')
        if not name:
            return Response({'error': 'Ім\'я обов\'язкове'}, status=status.HTTP_400_BAD_REQUEST)
        media_file.file_name = name
        media_file.save(update_fields=['file_name'])
        return Response(MediaFileSerializer(media_file).data)

    @action(detail=True, methods=['patch'])
    def move(self, request, pk=None):
        media_file = self.get_object()
        if media_file.user != request.user:
            return Response({'error': 'Доступ заборонено'}, status=status.HTTP_403_FORBIDDEN)
        collection_id = request.data.get('collection_id')
        if collection_id:
            collection = get_object_or_404(Collection, pk=collection_id, user=request.user)
            media_file.collection = collection
        else:
            media_file.collection = None
        media_file.save(update_fields=['collection'])
        return Response(MediaFileSerializer(media_file).data)

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        media_file = self.get_object()
        if media_file.user != request.user:
            return Response({'error': 'Доступ заборонено'}, status=status.HTTP_403_FORBIDDEN)
        token = media_file.generate_share_token()
        return Response({'share_token': token})

    @action(detail=False, methods=['post'], url_path='batch-delete')
    def batch_delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'Потрібен масив ids'}, status=status.HTTP_400_BAD_REQUEST)
        deleted = MediaFile.objects.filter(id__in=ids, user=request.user).delete()
        return Response({'deleted': deleted[0]})

    @action(detail=False, methods=['post'], url_path='bulk-upload')
    def bulk_upload(self, request):
        files = request.FILES.getlist('files')
        if not files:
            return Response({'error': 'Потрібні файли'}, status=status.HTTP_400_BAD_REQUEST)

        max_size = getattr(django_settings, 'MAX_UPLOAD_SIZE', 100 * 1024 * 1024)
        collection_id = request.data.get('collection')
        created = []

        for file_obj in files:
            if file_obj.size > max_size:
                continue

            media_file = MediaFile.objects.create(
                user=request.user,
                file=file_obj,
                file_name=file_obj.name,
                file_size=file_obj.size,
                mime_type=file_obj.content_type or mimetypes.guess_type(file_obj.name)[0] or 'application/octet-stream',
                collection_id=collection_id,
            )
            generate_preview(media_file)
            created.append(MediaFileSerializer(media_file).data)

        return Response({'created': len(created), 'files': created}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='index-local')
    def index_local(self, request):
        file_path = request.data.get('file_path')
        if not file_path:
            return Response({'error': 'Відсутній file_path'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Normalize path for the current OS (handle both / and \)
        normalized_path = os.path.normpath(file_path)
        
        if not os.path.exists(normalized_path):
            return Response({
                'error': 'Файл не знайдено на сервері',
                'tried_path': normalized_path,
                'original_path': file_path
            }, status=status.HTTP_400_BAD_REQUEST)

        file_name = os.path.basename(normalized_path)
        mime_type, _ = mimetypes.guess_type(normalized_path)
        file_size = os.path.getsize(normalized_path)

        media_file = MediaFile.objects.create(
            user=request.user,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type or 'application/octet-stream',
            visibility=request.data.get('visibility', 'private'),
            collection_id=request.data.get('collection')
        )

        generate_preview(media_file)
        serializer = self.get_serializer(media_file)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SharedFileView(viewsets.GenericViewSet):
    """Access file by share token (no auth required)."""
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='(?P<token>[a-f0-9]+)')
    def by_token(self, request, token=None):
        media_file = get_object_or_404(MediaFile, share_token=token)
        return Response(MediaFileSerializer(media_file).data)


class ExplorerViewSet(viewsets.ViewSet):
    """Browsing the node's local filesystem."""
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        path = request.query_params.get('path', os.getcwd())
        if not os.path.exists(path):
            return Response({'error': 'Path does not exist'}, status=404)
        
        try:
            items = []
            # Add parent dir entry
            parent = os.path.dirname(path)
            if parent != path:
                items.append({
                    'name': '..',
                    'path': parent,
                    'is_dir': True,
                    'size': 0
                })

            for entry in os.scandir(path):
                # Hide hidden files
                if entry.name.startswith('.'):
                    continue
                
                try:
                    info = {
                        'name': entry.name,
                        'path': entry.path,
                        'is_dir': entry.is_dir(),
                        'size': entry.stat().st_size if entry.is_file() else 0
                    }
                    items.append(info)
                except (PermissionError, OSError):
                    continue
            
            # Sort: dirs first, then files
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            
            return Response({
                'current_path': path,
                'items': items
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)
