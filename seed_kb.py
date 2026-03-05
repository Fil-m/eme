import sys
import os

# To allow running directly or via manage.py shell
# We assume it runs inside manage.py shell for simplicity

print("Seeding Knowledge Base from legacy eme_app data...")

try:
    sys.path.append(r"d:\dev\eme_app")
    from knowledge_base import KNOWLEDGE_BASE
except ImportError as e:
    print(f"Error importing legacy KB: {e}")
    sys.exit(1)

from eme_kb.models import KBCategory, KBArticle

# 1. Create Core Categories
cat_manifest, _ = KBCategory.objects.get_or_create(name="Eme Base", defaults={'emoji': '📖', 'order': 1})
cat_guides, _ = KBCategory.objects.get_or_create(name="Інструкції", defaults={'emoji': '🛠️', 'order': 2})

# Map legacy keys to categories and emojis
cat_mapping = {
    "manifest": (cat_manifest, "📜"),
    "responsibility": (cat_manifest, "⚖️"),
    "elements": (cat_manifest, "🔥"),
    "hubs": (cat_manifest, "🏝️"),
    "protocol": (cat_manifest, "🔄"),
    "codex": (cat_manifest, "⚖️"),
    "experience_board": (cat_manifest, "📋"),
    "support": (cat_manifest, "🫂"),
    "expansion": (cat_manifest, "🌱"),
    "installation": (cat_guides, "💻"),
    "mesh-guide": (cat_guides, "🌐"),
}

uk_data = KNOWLEDGE_BASE.get('uk', {})

for key, data in uk_data.items():
    title = data.get('title', 'Unknown')
    content = data.get('content', '')
    
    if key in cat_mapping:
        category, emoji = cat_mapping[key]
    else:
        category = cat_manifest
        emoji = "📖"
    
    # Prefix title with emoji to keep it visible if needed, or just keep title
    # Actually KBCategory has emoji, but KBArticle doesn't. 
    article, created = KBArticle.objects.update_or_create(
        title=title,
        defaults={
            'content': content,
            'category': category,
            'tags': key,
            'is_published': True
        }
    )
    print(f"{'Created' if created else 'Updated'} article: {title}")

print("KB Seeding complete!")
