import os
import zipfile
import io
import socket
import json
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status


class IPDiscoveryView(APIView):
    """Detects the local network IP of the server."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception:
            ip = "127.0.0.1"
        return Response({'ip': ip})


# Module dependencies: if you select a module, these must come too
MODULE_DEPS = {
    'eme_kb': [],
    'eme_chat': ['eme_media'],
    'eme_ai': ['projects'],
    'projects': [],
    'network': [],
    'clone_master': [],
    'eme_nav': [],
    'eme_media': [],
    'profiles': [],
    'system_settings': [],
    'eme': [],  # core configs
}

MODULE_META = {
    'eme': {'icon': '⚙️', 'desc': 'Основний конфіг Django (обов\'язковий)'},
    'profiles': {'icon': '👤', 'desc': 'Профілі та авторизація'},
    'system_settings': {'icon': '🔧', 'desc': 'Системні налаштування'},
    'eme_nav': {'icon': '🧭', 'desc': 'Навігація і бокова панель'},
    'eme_media': {'icon': '🖼️', 'desc': 'Завантаження медіа-файлів'},
    'network': {'icon': '🌐', 'desc': 'Mesh-мережа і heartbeat'},
    'clone_master': {'icon': '📦', 'desc': 'Клонування системи'},
    'projects': {'icon': '📋', 'desc': 'Проекти і задачі'},
    'eme_ai': {'icon': '🤖', 'desc': 'AI-модуль (потребує Ollama)'},
    'eme_kb': {'icon': '📚', 'desc': 'База Знань'},
    'eme_chat': {'icon': '💬', 'desc': 'Чат (групи, DM, стікери)'},
}

# Auto-included seed scripts per module
MODULE_SEEDS = {
    'eme_nav': ['seed_nav.py'],
    'eme_kb': ['seed_kb.py'],
    'eme_chat': ['seed_chat.py'],
}


class ModuleListView(APIView):
    """Returns a list of local project modules available for cloning."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        base_dir = settings.BASE_DIR
        modules = []
        skip = {'django', 'rest_framework', 'corsheaders', 'rest_framework_simplejwt'}
        
        for app in settings.INSTALLED_APPS:
            app_name = app.split('.')[-1]
            if app_name in skip or app.startswith('django.contrib'):
                continue
            app_path = os.path.join(base_dir, app_name)
            
            if os.path.isdir(app_path):
                meta = MODULE_META.get(app_name, {})
                modules.append({
                    'id': app_name,
                    'name': app_name.replace('_', ' ').title(),
                    'icon': meta.get('icon', '📁'),
                    'desc': meta.get('desc', ''),
                    'deps': MODULE_DEPS.get(app_name, []),
                    'is_system': app_name in {'eme', 'profiles', 'system_settings', 'eme_nav'},
                })
                
        return Response(modules)


class CloneCreateView(APIView):
    """Generates a ZIP archive of selected modules."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        selected_modules = request.data.get('modules', [])
        include_db = request.data.get('include_db', False)
        include_media = request.data.get('include_media', False)
        include_seeds = request.data.get('include_seeds', True)
        clone_name = request.data.get('clone_name', '').strip() or f"clone_{datetime.now().strftime('%Y%m%d_%H%M')}"

        if not selected_modules:
            return Response({'error': 'No modules selected'}, status=status.HTTP_400_BAD_REQUEST)

        # Auto-add core requirements
        core_required = ['eme', 'profiles', 'system_settings', 'eme_nav']
        all_modules = list(set(selected_modules + core_required))

        # Auto-resolve deps
        for m in selected_modules:
            for dep in MODULE_DEPS.get(m, []):
                if dep not in all_modules:
                    all_modules.append(dep)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. CORE FILES
            core_files = ['manage.py', 'requirements.txt', 'start.sh', 'start.bat', 'bootstrap_eme.sh', 'README.md']
            for f in core_files:
                f_path = os.path.join(settings.BASE_DIR, f)
                if os.path.exists(f_path):
                    zf.write(f_path, f)

            # 2. SELECTED MODULES
            for module in all_modules:
                module_path = os.path.join(settings.BASE_DIR, module)
                if os.path.isdir(module_path):
                    for root, dirs, files in os.walk(module_path):
                        if any(x in root for x in ['__pycache__', 'venv', '.git', 'node_modules']):
                            continue
                        for file in files:
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, settings.BASE_DIR)
                            zf.write(full_path, rel_path)

            # 3. STATIC & TEMPLATES
            for folder in ['static', 'templates']:
                folder_path = os.path.join(settings.BASE_DIR, folder)
                if os.path.isdir(folder_path):
                    for root, dirs, files in os.walk(folder_path):
                        if any(x in root for x in ['__pycache__', '.git']):
                            continue
                        for file in files:
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, settings.BASE_DIR)
                            zf.write(full_path, rel_path)

            # 4. SEED SCRIPTS
            if include_seeds:
                for mod in all_modules:
                    for seed_file in MODULE_SEEDS.get(mod, []):
                        seed_path = os.path.join(settings.BASE_DIR, seed_file)
                        if os.path.exists(seed_path):
                            zf.write(seed_path, seed_file)

            # 5. DATABASE (optional)
            if include_db:
                db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
                if os.path.exists(db_path):
                    zf.write(db_path, 'db.sqlite3')

            # 6. MEDIA (optional)
            if include_media:
                media_path = settings.MEDIA_ROOT
                if os.path.isdir(media_path):
                    for root, dirs, files in os.walk(media_path):
                        if any(x in root for x in ['clones', '__pycache__']):
                            continue
                        for file in files:
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, settings.BASE_DIR)
                            zf.write(full_path, rel_path)

            # 7. MANIFEST
            manifest_data = {
                'eme_version': '2.0',
                'clone_name': clone_name,
                'generated_by': request.user.username,
                'generated_at': datetime.now().isoformat(),
                'modules': all_modules,
                'include_db': include_db,
                'include_media': include_media,
                'include_seeds': include_seeds,
            }
            manifest_md = f"""# EME OS — Clone Manifest

**Clone:** {clone_name}
**Generated by:** {request.user.username}
**Date:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

## Included Modules
{chr(10).join(f'- {m}' for m in all_modules)}

## Setup Instructions (Termux)
```bash
termux-setup-storage
pkg update -y
pkg install -y python curl unzip git libjpeg-turbo libpng
unzip clone.zip -d eme && cd eme
bash start.sh
```

## Notes
This is an auto-generated partial clone of EME OS.
"""
            zf.writestr('CLONE_INFO.md', manifest_md)
            zf.writestr('clone_manifest.json', json.dumps(manifest_data, ensure_ascii=False, indent=2))

        buffer.seek(0)
        
        clones_dir = os.path.join(settings.MEDIA_ROOT, 'clones')
        os.makedirs(clones_dir, exist_ok=True)
        
        safe_name = "".join(c for c in clone_name if c.isalnum() or c in ('_', '-'))
        filename = f"eme_{safe_name}.zip"
        file_path = os.path.join(clones_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(buffer.getvalue())
            
        file_url = f"{settings.MEDIA_URL}clones/{filename}"
        size_kb = os.path.getsize(file_path) // 1024
        
        return Response({
            'url': file_url,
            'filename': filename,
            'message': 'Клон успішно створено',
            'modules_count': len(all_modules),
            'size_kb': size_kb,
        })
