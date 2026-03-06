import os
import django
from django.utils import timezone
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eme.settings')
django.setup()

from eme_media.models import Collection

def debug_datetimes():
    now = timezone.now()
    print(f"Current timezone.now(): {now}")
    
    col = Collection.objects.order_by('-created_at').first()
    if col:
        print(f"Latest collection: {col.name}")
        print(f"Created at: {col.created_at}")
        
        since_ts = datetime.now().timestamp() - 3600 # 1 hour ago
        since_dt = datetime.fromtimestamp(since_ts)
        if timezone.is_aware(now):
            since_dt = timezone.make_aware(since_dt)
            
        print(f"Testing filter since_dt: {since_dt}")
        
        match = Collection.objects.filter(created_at__gt=since_dt, id=col.id).exists()
        print(f"Filter match (created_at__gt=since_dt): {match}")
    else:
        print("No collections found.")

if __name__ == '__main__':
    debug_datetimes()
