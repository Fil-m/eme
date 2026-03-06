import requests
from django.conf import settings
from profiles.models import EMEUser, WallPost, WallComment
from eme_chat.models import Message, ChatRoom
from network.models import Node
import time
from urllib.parse import urljoin

SYNC_PORT = 8000  # Default port for development. Should probably be dynamic or configurable.

def get_or_create_user(username):
    """Fetches a user locally by username, or creates a placeholder if missing."""
    if not username:
        return None
    user, created = EMEUser.objects.get_or_create(
        username=username,
        defaults={
            'bio': 'Created via Mesh Sync',
            'is_active': False # Deactivated mostly to prevent login until they actually clone/register
        }
    )
    return user

def pull_and_save_object(source_ip, obj_type, sync_id):
    """Pulls a single object from a node and saves it locally."""
    try:
        url = f"http://{source_ip}:{SYNC_PORT}/api/network/sync/pull/?type={obj_type}&sync_id={sync_id}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            save_synced_object(obj_type, data)
    except Exception as e:
        print(f"Failed to pull {obj_type} {sync_id} from {source_ip}: {e}")


def catchup_with_node(source_ip, last_sync_at):
    """Pulls all missed objects from a node since last_sync_at."""
    try:
        ts = last_sync_at.timestamp() if last_sync_at else 0
        url = f"http://{source_ip}:{SYNC_PORT}/api/network/sync/catchup/?since={ts}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get('items', []):
                save_synced_object(item['type'], item['data'])
                
            # Update last_sync_at locally
            Node.objects.filter(ip_address=source_ip).update(last_sync_at=time.localtime())
    except Exception as e:
        print(f"Failed catchup with {source_ip}: {e}")

def save_synced_object(obj_type, data):
    """Saves a JSON object payload into the local database without conflicts."""
    try:
        if obj_type == 'wallpost':
            owner = get_or_create_user(data.get('owner_username'))
            author = get_or_create_user(data.get('author_username'))
            
            WallPost.objects.update_or_create(
                sync_id=data['sync_id'],
                defaults={
                    'owner': owner,
                    'author': author,
                    'content': data.get('content', ''),
                    'created_at': data.get('created_at'),
                    'likes_count': data.get('likes_count', 0)
                }
            )
            
        elif obj_type == 'wallcomment':
            post = WallPost.objects.filter(sync_id=data.get('post_sync_id')).first()
            if not post:
                return # Cannot sync comment if post doesn't exist locally
            author = get_or_create_user(data.get('author_username'))
            
            WallComment.objects.update_or_create(
                sync_id=data['sync_id'],
                defaults={
                    'post': post,
                    'author': author,
                    'content': data.get('content', ''),
                    'created_at': data.get('created_at')
                }
            )
            
        elif obj_type == 'chatmessage':
            room_id = data.get('room_id')
            room = ChatRoom.objects.filter(id=room_id).first()
            if not room:
                return # Cannot sync message if we don't know the room
                
            sender = get_or_create_user(data.get('sender_username'))
            
            Message.objects.update_or_create(
                id=data['id'],
                defaults={
                    'room': room,
                    'sender': sender,
                    'text': data.get('text', ''),
                    'is_read': data.get('is_read', False),
                    'created_at': data.get('created_at')
                }
            )
            
    except Exception as e:
        print(f"Error saving synced object {obj_type}: {e}")
