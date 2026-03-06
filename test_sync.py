import os
import django
import sys
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eme.settings')
django.setup()

from rest_framework.test import APIClient
from profiles.models import EMEUser, WallPost, WallComment
from eme_chat.models import Message, ChatRoom
from network.models import Node

def run_sync_test():
    client = APIClient()
    
    # Create test data
    user, _ = EMEUser.objects.get_or_create(username="SyncTestUser")
    client.force_authenticate(user=user)
    
    # 1. Create a Post
    post = WallPost.objects.create(author=user, owner=user, content="Sync Test Post")
    print(f"Post created, sync_id={post.sync_id}")
    
    # 2. Test Pull View
    print("\n--- Testing Pull View ---")
    resp = client.get(f'/api/network/sync/pull/?type=wallpost&sync_id={post.sync_id}')
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(resp.json())
        
    # 3. Test Catchup View
    print("\n--- Testing Catchup View ---")
    resp = client.get('/api/network/sync/catchup/?since=0')
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        items = resp.json().get('items', [])
        print(f"Got {len(items)} items in catchup.")
        if len(items) > 0:
            print(f"First item: {items[0]}")

if __name__ == '__main__':
    run_sync_test()
