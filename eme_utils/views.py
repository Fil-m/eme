import random
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from bs4 import BeautifulSoup
import requests
import psutil

from .models import Bookmark, PastebinSnippet, Memo
from .serializers import BookmarkSerializer, PastebinSnippetSerializer, MemoSerializer

class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bookmark.objects.filter(user_id=self.request.user.id).order_by('-created_at')

    def perform_create(self, serializer):
        url = serializer.validated_data.get('url')
        title = serializer.validated_data.get('title', '')
        description = serializer.validated_data.get('description', '')
        
        # Try to auto-fetch title if missing
        if not title and url:
            try:
                res = requests.get(url, timeout=3)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.content, 'html.parser')
                    if soup.title:
                        title = soup.title.string.strip()
                    # optionally fetch description from meta tag
                    if not description:
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        if meta_desc and meta_desc.get('content'):
                            description = meta_desc['content'].strip()
            except Exception:
                pass
                
        serializer.save(user_id=self.request.user.id, title=title, description=description)

class PastebinSnippetViewSet(viewsets.ModelViewSet):
    serializer_class = PastebinSnippetSerializer
    # Allow read for anyone if public, but create requires auth
    
    def get_permissions(self):
        if self.action in ['list', 'create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        # retrieve can be public if the snippet is public
        return [permissions.AllowAny()]

    def get_queryset(self):
        if self.action == 'retrieve':
            return PastebinSnippet.objects.all()
        return PastebinSnippet.objects.filter(user_id=self.request.user.id).order_by('-created_at')

    def perform_create(self, serializer):
        # generate short code
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        serializer.save(user_id=self.request.user.id, short_code=code)

    @action(detail=False, methods=['get'], url_path='by_code/(?P<code>[^/.]+)')
    def by_code(self, request, code=None):
        try:
            snippet = PastebinSnippet.objects.get(short_code=code)
            if not snippet.is_public and snippet.user_id != request.user.id:
                return Response({'error': 'Private snippet'}, status=403)
            return Response(self.get_serializer(snippet).data)
        except PastebinSnippet.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

class MemoViewSet(viewsets.ModelViewSet):
    serializer_class = MemoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Memo.objects.filter(user_id=self.request.user.id).order_by('-is_pinned', '-created_at')

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)

class SysMonView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            data = {
                'cpu': psutil.cpu_percent(interval=None),
                'cpu_cores': psutil.cpu_count(logical=True),
                'ram_total': getattr(psutil.virtual_memory(), 'total', 0),
                'ram_used': getattr(psutil.virtual_memory(), 'used', 0),
                'ram_percent': getattr(psutil.virtual_memory(), 'percent', 0),
                'disk_total': getattr(psutil.disk_usage('/'), 'total', 0),
                'disk_used': getattr(psutil.disk_usage('/'), 'used', 0),
                'disk_percent': getattr(psutil.disk_usage('/'), 'percent', 0),
                'boot_time': psutil.boot_time()
            }
        except Exception as e:
            data = {'error': str(e)}
        return Response(data)
