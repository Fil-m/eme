import os
import django
import sys
import uuid
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eme.settings')
django.setup()

from rest_framework.test import APIClient
from profiles.models import EMEUser
from eme_media.models import Collection, MediaFile
from projects.models import Project, ProjectAction, ProjectRole, ProjectMember
from network.sync_service import save_synced_object

def test_media_sync():
    print("\n--- Testing Media Sync ---")
    client = APIClient()
    user, _ = EMEUser.objects.get_or_create(username="MediaTestUser")
    
    # 1. Test Collection Sync
    col = Collection.objects.create(user=user, name="Sync Test Collection")
    print(f"Collection created: {col.name}, sync_id={col.sync_id}")
    
    resp = client.get(f'/api/network/sync/pull/?type=collection&sync_id={col.sync_id}')
    assert resp.status_code == 200
    print(f"Collection Pull SUCCESS: {resp.json()['name']}")
    
    # 2. Test MediaFile Sync
    mf = MediaFile.objects.create(user=user, collection=col, file_name="test_image.jpg", mime_type="image/jpeg")
    print(f"MediaFile created: {mf.file_name}, sync_id={mf.sync_id}")
    
    resp = client.get(f'/api/network/sync/pull/?type=mediafile&sync_id={mf.sync_id}')
    assert resp.status_code == 200
    print(f"MediaFile Pull SUCCESS: {resp.json()['file_name']}")

def test_project_sync():
    print("\n--- Testing Project Sync ---")
    client = APIClient()
    user, _ = EMEUser.objects.get_or_create(username="ProjectTestUser")
    
    # 1. Test Project Sync
    project = Project.objects.create(owner=user, title="Sync Test Project")
    print(f"Project created: {project.title}, sync_id={project.sync_id}")
    
    resp = client.get(f'/api/network/sync/pull/?type=project&sync_id={project.sync_id}')
    assert resp.status_code == 200
    print(f"Project Pull SUCCESS: {resp.json()['title']}")
    
    # 2. Test Project Action Sync
    action = ProjectAction.objects.create(project=project, text="Test Action Item")
    print(f"Action created: {action.text}, sync_id={action.sync_id}")
    
    resp = client.get(f'/api/network/sync/pull/?type=projectaction&sync_id={action.sync_id}')
    assert resp.status_code == 200
    print(f"Action Pull SUCCESS: {resp.json()['text']}")

def test_catchup_extended():
    print("\n--- Testing Extended Catchup ---")
    client = APIClient()
    from django.utils import timezone
    # Request everything since 1 minute ago in UTC
    since_ts = timezone.now().timestamp() - 60
    resp = client.get(f'/api/network/sync/catchup/?since={since_ts}')
    assert resp.status_code == 200
    items = resp.json().get('items', [])
    print(f"Got {len(items)} items in catchup.")
    
    types_found = set(item['type'] for item in items)
    print(f"Types in catchup: {types_found}")
    
    expected_types = {'collection', 'mediafile', 'project', 'projectaction'}
    found_expected = expected_types.intersection(types_found)
    print(f"Newly implemented types found: {found_expected}")

if __name__ == '__main__':
    try:
        test_media_sync()
        test_project_sync()
        test_catchup_extended()
        print("\nALL EXTENDED SYNC TESTS PASSED!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
