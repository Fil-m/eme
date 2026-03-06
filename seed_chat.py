"""
Seed script for eme_chat:
- Creates the global 'general' chat room visible to everyone
Run with: python manage.py shell -c "exec(open('seed_chat.py', encoding='utf-8').read())"
"""
from eme_chat.models import ChatRoom

GENERAL_ROOM_TITLE = "🌐 Загальний EME"

# Fixed UUID for General room to be consistent across all mesh nodes
GENERAL_ROOM_ID = "00000000-0000-0000-0000-000000000001"

room, created = ChatRoom.objects.get_or_create(
    id=GENERAL_ROOM_ID,
    defaults={
        'kind': 'general',
        'title': GENERAL_ROOM_TITLE,
        'description': 'Загальний чат для всіх учасників мережі EME.'
    }
)

if created:
    print(f"Created general room: {room.title}")
else:
    print(f"General room already exists: {room.title}")

print(f"Room ID: {room.id}")
