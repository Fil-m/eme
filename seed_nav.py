from eme_nav.models import NavItem

items = [
    dict(item_id='my_page',    icon='👤', label='Моя сторінка', order=0, url='my_page'),
    dict(item_id='settings',   icon='⚙️',  label='Налаштування',  order=1, url='settings'),
    dict(item_id='gallery',    icon='🖼️',  label='Галерея',     order=2, url='gallery'),
    dict(item_id='apps_store', icon='🧩',  label='Додатки',       order=3, url='apps_store'),
    dict(item_id='projects',   icon='📋',  label='Проекти',       order=4, url='projects'),
    dict(item_id='network',    icon='🌐',  label='Мережа',        order=5, url='network'),
    dict(item_id='clone_master', icon='📦', label='Клон Мастер',   order=6, url='clone_master'),
    dict(item_id='kb',         icon='📚',  label='База Знань',    order=7, url='kb'),
    dict(item_id='chat',       icon='💬',  label='Чат',           order=8, url='chat'),
]

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
    print(f"{'created' if created else 'updated'}: {obj.item_id} {obj.icon}")
    print(f"{'created' if created else 'updated'}: {obj.item_id} {obj.icon}")

print("Done")
