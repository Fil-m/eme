from django.core.management.base import BaseCommand
from eme_nav.models import NavItem

class Command(BaseCommand):
    help = 'Seeds the database with default navigation items'

    def handle(self, *args, **kwargs):
        items = [
            # GROUPS
            dict(item_id='social_group', icon='👥', label='Соціальне', order=0, url='', parent_id=None),
            dict(item_id='system_group', icon='⚙️', label='Система',   order=10, url='', parent_id=None),
            dict(item_id='apps_group',   icon='🧩', label='Додатки',   order=20, url='', parent_id=None),

            # SOCIAL
            dict(item_id='my_page',    icon='👤', label='Моя сторінка', order=1, url='my_page', parent_id='social_group'),
            dict(item_id='chat',       icon='💬', label='Чат',           order=2, url='chat',    parent_id='social_group'),
            dict(item_id='network',    icon='🌐', label='Мережа',        order=3, url='network', parent_id='social_group'),

            # SYSTEM
            dict(item_id='projects',   icon='📋', label='Проєкти',       order=11, url='projects', parent_id='system_group'),

            # APPS
            dict(item_id='apps_store', icon='🏪', label='Магазин',       order=21, url='apps_store', parent_id='apps_group'),
        ]

        # First, clear extra items not in this list to keep it clean
        valid_ids = [d['item_id'] for d in items]
        NavItem.objects.exclude(item_id__in=valid_ids).delete()

        count = 0
        # Map item_id to database objects for parent links
        lookup = {}
        
        # Two passes: first for parents, then for children
        for d in sorted(items, key=lambda x: 0 if x['parent_id'] is None else 1):
            parent = lookup.get(d['parent_id']) if d.get('parent_id') else None
            obj, created = NavItem.objects.update_or_create(
                item_id=d['item_id'], 
                defaults={
                    'icon': d['icon'],
                    'label': d['label'],
                    'order': d['order'],
                    'url': d['url'],
                    'parent': parent
                }
            )
            lookup[d['item_id']] = obj
            count += 1
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} nav item: {obj.label}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} nav items'))
