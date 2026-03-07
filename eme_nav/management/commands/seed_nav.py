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
            dict(item_id='projects',     icon='📋', label='Проєкти',       order=11, url='projects',     parent_id='system_group'),
            dict(item_id='kb',           icon='📚', label='База Знань',    order=12, url='kb',           parent_id='system_group'),
            dict(item_id='clone_master', icon='📦', label='Клон Мастер',   order=13, url='clone_master', parent_id='system_group'),

            # APPS
            dict(item_id='apps_store',      icon='🏪', label='Магазин',       order=21, url='apps_store',      parent_id='apps_group'),
            dict(item_id='park_adventures', icon='🏹', label='Парк Пригод',   order=22, url='park_adventures', parent_id='apps_group'),
            dict(item_id='qr_generator',    icon='🤳', label='Генератор QR',  order=23, url='qr_generator',    parent_id='apps_group'),
        ]

        # We no longer delete excluded items to allow manual additions
        # valid_ids = [d['item_id'] for d in items]
        # NavItem.objects.exclude(item_id__in=valid_ids).delete()

        count = 0
        lookup = {}
        
        # Two passes: first for parents, then for children
        for d in sorted(items, key=lambda x: 0 if x['parent_id'] is None else 1):
            parent = lookup.get(d['parent_id']) if d.get('parent_id') else None
            
            # Check if exists to avoid mangling existing manual data if not needed
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
            # Using simple ASCII for logging to avoid terminal encoding errors
            self.stdout.write(self.style.SUCCESS(f'{action} nav item: {d["item_id"]}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} nav items'))
