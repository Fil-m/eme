from django.contrib import admin
from .models import NavItem, UserNavAccess


@admin.register(NavItem)
class NavItemAdmin(admin.ModelAdmin):
    list_display = ['icon', 'label', 'item_id', 'url', 'order', 'is_active', 'parent', 'badge_count', 'visible_to_all']
    list_editable = ['order', 'is_active', 'badge_count', 'visible_to_all']
    list_filter = ['is_active', 'visible_to_all']
    search_fields = ['label', 'item_id']
    ordering = ['order']


@admin.register(UserNavAccess)
class UserNavAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'nav_item']
    list_filter = ['nav_item']
