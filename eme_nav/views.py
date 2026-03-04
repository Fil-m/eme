from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import NavItem, UserNavAccess
from .serializers import NavItemSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_node_admin


class NavItemViewSet(viewsets.ModelViewSet):
    serializer_class = NavItemSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        qs = NavItem.objects.filter(is_active=True, parent__isnull=True)

        if not user.is_node_admin:
            qs = qs.filter(
                Q(visible_to_all=True) |
                Q(user_access__user=user)
            ).distinct()

        return qs.order_by('order')

    @action(detail=True, methods=['patch'], url_path='badge')
    def update_badge(self, request, pk=None):
        nav_item = self.get_object()
        count = request.data.get('badge_count', 0)
        nav_item.badge_count = int(count)
        nav_item.save(update_fields=['badge_count'])
        return Response({'badge_count': nav_item.badge_count})
