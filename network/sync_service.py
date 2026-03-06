import requests
from django.conf import settings
from profiles.models import EMEUser, WallPost, WallComment
from eme_chat.models import Message, ChatRoom
from network.models import Node
import time
from django.utils import timezone
from urllib.parse import urljoin
import threading

SYNC_PORT = 8000  # Default port for development. Should probably be dynamic or configurable.
db_lock = threading.Lock()

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
            with db_lock:
                save_synced_object(obj_type, data, source_ip=source_ip)
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
            with db_lock:
                for item in data.get('items', []):
                    save_synced_object(item['type'], item['data'], source_ip=source_ip)
                
                # Update last_sync_at locally
                Node.objects.filter(ip_address=source_ip).update(last_sync_at=timezone.now())
    except Exception as e:
        print(f"Failed catchup with {source_ip}: {e}")

def save_synced_object(obj_type, data, source_ip=None):
    """Saves a JSON object payload into the local database without conflicts."""
    try:
        if obj_type == 'user':
            EMEUser.objects.update_or_create(
                username=data['username'],
                defaults={
                    'first_name': data.get('first_name', ''),
                    'last_name': data.get('last_name', ''),
                    'bio': data.get('bio', ''),
                    'level': data.get('level', 1),
                    'points': data.get('points', 0),
                }
            )
            
        elif obj_type == 'wallpost':
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
                # If room is missing, we might need to pull it, but for now we skip 
                # or wait for catchup to bring rooms first.
                return 
                
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

        elif obj_type == 'chatroom':
            from eme_chat.models import ChatRoom
            creator = get_or_create_user(data.get('creator_username'))
            ChatRoom.objects.update_or_create(
                id=data['id'],
                defaults={
                    'kind': data.get('kind', 'group'),
                    'title': data.get('title', ''),
                    'creator': creator,
                    'description': data.get('description', ''),
                    'created_at': data.get('created_at')
                }
            )

        elif obj_type == 'roommember':
            from eme_chat.models import ChatRoom, RoomMember
            room = ChatRoom.objects.filter(id=data.get('room_id')).first()
            if not room: return
            user = get_or_create_user(data.get('user_username'))
            
            RoomMember.objects.update_or_create(
                sync_id=data['sync_id'],
                defaults={
                    'room': room,
                    'user': user,
                    'role': data.get('role', 'member'),
                    'joined_at': data.get('joined_at')
                }
            )
            
        elif obj_type == 'collection':
            from eme_media.models import Collection
            user = get_or_create_user(data.get('user_username'))
            parent = None
            if data.get('parent_sync_id'):
                parent = Collection.objects.filter(sync_id=data['parent_sync_id']).first()
                
            Collection.objects.update_or_create(
                sync_id=data['sync_id'],
                defaults={
                    'user': user,
                    'name': data.get('name', ''),
                    'description': data.get('description', ''),
                    'parent': parent,
                    'created_at': data.get('created_at')
                }
            )
            
        elif obj_type == 'project':
            from projects.models import Project
            owner = get_or_create_user(data.get('owner_username'))
            
            Project.objects.update_or_create(
                sync_id=data['sync_id'],
                defaults={
                    'owner': owner,
                    'title': data.get('title', ''),
                    'description': data.get('description', ''),
                    'emoji': data.get('emoji', '📋'),
                    'domain': data.get('domain', 'eme'),
                    'status': data.get('status', 'backlog'),
                    'priority': data.get('priority', 'medium'),
                    'deadline': data.get('deadline'),
                    'next_action': data.get('next_action', ''),
                    'is_public': data.get('is_public', True),
                    'order': data.get('order', 0),
                    'created_at': data.get('created_at'),
                    'updated_at': data.get('updated_at')
                }
            )
            
        elif obj_type == 'projectrole':
            from projects.models import Project, ProjectRole
            proj = Project.objects.filter(sync_id=data.get('project_sync_id')).first()
            if not proj: return
            
            ProjectRole.objects.update_or_create(
                sync_id=data['sync_id'],
                defaults={
                    'project': proj,
                    'name': data.get('name', ''),
                    'emoji': data.get('emoji', '👤'),
                    'description': data.get('description', ''),
                    'created_at': data.get('created_at')
                }
            )
            
        elif obj_type == 'projectmember':
            from projects.models import Project, ProjectRole, ProjectMember
            proj = Project.objects.filter(sync_id=data.get('project_sync_id')).first()
            if not proj: return
            user = get_or_create_user(data.get('user_username'))
            role = None
            if data.get('role_sync_id'):
                role = ProjectRole.objects.filter(sync_id=data['role_sync_id']).first()
                
            ProjectMember.objects.update_or_create(
                sync_id=data['sync_id'],
                defaults={
                    'project': proj,
                    'user': user,
                    'role': role,
                    'joined_at': data.get('joined_at')
                }
            )
            
        elif obj_type == 'projectaction':
            from projects.models import Project, ProjectRole, ProjectMember, ProjectAction
            proj = Project.objects.filter(sync_id=data.get('project_sync_id')).first()
            if not proj: return
            
            depends_on = None
            if data.get('depends_on_sync_id'):
                depends_on = ProjectAction.objects.filter(sync_id=data['depends_on_sync_id']).first()
                
            assignee = None
            if data.get('assignee_sync_id'):
                assignee = ProjectMember.objects.filter(sync_id=data['assignee_sync_id']).first()
                
            assignee_role = None
            if data.get('assignee_role_sync_id'):
                assignee_role = ProjectRole.objects.filter(sync_id=data['assignee_role_sync_id']).first()
                
            ProjectAction.objects.update_or_create(
                sync_id=data['sync_id'],
                defaults={
                    'project': proj,
                    'text': data.get('text', ''),
                    'status': data.get('status', 'todo'),
                    'is_done': data.get('is_done', False),
                    'priority': data.get('priority', 'medium'),
                    'deadline': data.get('deadline'),
                    'due_date': data.get('due_date'),
                    'depends_on': depends_on,
                    'assignee': assignee,
                    'assignee_role': assignee_role,
                    'created_at': data.get('created_at')
                }
            )
            
        elif obj_type == 'mediafile':
            from eme_media.models import MediaFile, Collection
            from django.core.files.base import ContentFile
            import os
            
            user = get_or_create_user(data.get('user_username'))
            collection = None
            if data.get('collection_sync_id'):
                collection = Collection.objects.filter(sync_id=data['collection_sync_id']).first()
                
            mf, created = MediaFile.objects.update_or_create(
                sync_id=data['sync_id'],
                defaults={
                    'user': user,
                    'collection': collection,
                    'file_name': data.get('file_name', ''),
                    'file_size': data.get('file_size', 0),
                    'mime_type': data.get('mime_type', ''),
                    'visibility': data.get('visibility', 'private'),
                    'created_at': data.get('created_at')
                }
            )
            
            # Now download the actual file if it has one and we don't have it locally yet
            # Or if it was just created
            if source_ip and data.get('file_url') and not mf.file:
                try:
                    # Construct URL to download from the source node
                    # data['file_url'] is something like /media/uploads/2026/03/06/image.jpg
                    download_url = f"http://{source_ip}:{SYNC_PORT}{data['file_url']}"
                    resp = requests.get(download_url, stream=True, timeout=30)
                    
                    if resp.status_code == 200:
                        # Extract just the filename from the path
                        filename = os.path.basename(data['file_url'])
                        # Save the binary content
                        # Since we are inside update_or_create, it's safer to just set the file and save
                        mf.file.save(filename, ContentFile(resp.content), save=True)
                        print(f"Successfully downloaded media file {filename} from {source_ip}")
                        
                        # Generate preview locally for the newly downloaded file
                        from eme_media.utils import generate_preview
                        generate_preview(mf)
                    else:
                        print(f"Failed to download media file from {download_url}, status: {resp.status_code}")
                except Exception as e:
                    print(f"Error downloading media file {data['file_url']} from {source_ip}: {e}")
            
    except Exception as e:
        print(f"Error saving synced object {obj_type}: {e}")
