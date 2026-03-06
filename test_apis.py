import os
import django
import json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eme.settings")
django.setup()

from rest_framework.test import APIClient
from profiles.models import EMEUser

u, _ = EMEUser.objects.get_or_create(username='tester', email='tester@test.com')

client = APIClient()
client.force_authenticate(user=u)

print("== Testing Wall Post ==")
resp1 = client.post('/api/profiles/wall-posts/', {'content': 'Hello', 'owner': str(u.id)}, format='json')
print(resp1.status_code)
print(resp1.content.decode('utf-8'))

print("== Testing Media Files ==")
resp2 = client.get('/api/media/files/')
print(resp2.status_code)
print(resp2.content.decode('utf-8'))

print("== Testing Projects ==")
resp3 = client.get('/api/projects/')
print(resp3.status_code)
print(resp3.content.decode('utf-8'))

print("== Testing Network ==")
resp4 = client.get('/api/network/discovery/')
print(resp4.status_code)
print(resp4.content.decode('utf-8'))

print("== Testing Chat ==")
resp5 = client.get('/api/network/rooms/')
print(resp5.status_code)
print(resp5.content.decode('utf-8'))

print("== Testing Knowledge Base ==")
resp6 = client.get('/api/kb/nodes/')
print(resp6.status_code)
print(resp6.content.decode('utf-8'))
