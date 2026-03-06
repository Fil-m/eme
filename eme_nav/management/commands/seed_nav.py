from django.core.management.base import BaseCommand
from eme_nav.models import NavItem

class Command(BaseCommand):
    help = 'Seeds the database with default navigation items'

    def handle(self, *args, **kwargs):
        items = [
            dict(item_id='my_page',    icon='👤', label='Моя сторінка', order=0, url='my_page'),
            dict(item_id='projects',   icon='📋',  label='Проекти',       order=1, url='projects'),
            dict(item_id='network',    icon='🌐',  label='Мережа',        order=2, url='network'),
            dict(item_id='apps_store', icon='🧩',  label='Додатки',       order=3, url='apps_store'),
            dict(item_id='chat',       icon='💬',  label='Чат',           order=4, url='chat'),
        ]

        count = 0
        for d in items:
            obj, created = NavItem.objects.update_or_create(
                item_id=d['item_id'], 
                defaults={
                    'icon': d['icon'],
                    'label': d['label'],
                    'order': d['order'],
                    'url': d['url']
                }
            )
            count += 1
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} nav item: {obj.label}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {count} nav items'))
