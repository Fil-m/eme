from rest_framework import serializers
from .models import NavItem


class NavItemSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = NavItem
        fields = [
            'id', 'item_id', 'icon', 'label', 'url', 'order',
            'is_active', 'parent', 'badge_count', 'visible_to_all', 'children',
        ]
        read_only_fields = ['id']

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by('order')
        return NavItemSerializer(children, many=True).data
