import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eme.settings")
django.setup()

from rest_framework.test import APIClient
from profiles.models import EMEUser
import traceback

u = EMEUser.objects.first()
if u:
    client = APIClient()
    client.force_authenticate(user=u)
    try:
        resp = client.get('/api/nav/')
        print(f"Status: {resp.status_code}")
        print(resp.content.decode('utf-8'))
    except Exception as e:
        print("EXCEPTION:")
        traceback.print_exc()
else:
    print("No users found.")
