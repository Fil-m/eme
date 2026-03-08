from django.conf import settings
from rest_framework import generics, permissions
from .models import CoreSettings, UserAppLayout, AIDraftApp
from .serializers import CoreSettingsSerializer, UserAppLayoutSerializer, AIDraftAppSerializer
from .git_utils import push_app_to_git, auto_update_sync

class CoreSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = CoreSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, created = CoreSettings.objects.get_or_create(user=self.request.user)
        return obj


from rest_framework import viewsets
from .models import UserAppLayout
from .serializers import UserAppLayoutSerializer

class UserAppLayoutViewSet(viewsets.ModelViewSet):
    serializer_class = UserAppLayoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserAppLayout.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


import json
import urllib.request
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.text import slugify
from .models import AIDraftApp
from .serializers import AIDraftAppSerializer

class AIDraftAppViewSet(viewsets.ModelViewSet):
    serializer_class = AIDraftAppSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AIDraftApp.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AIAppGenerateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        prompt = request.data.get('prompt', '').strip()
        app_name = request.data.get('name', 'Generated App')
        if not prompt:
            return Response({'error': 'Пропмт не надано'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate component name from app_name
        slug = slugify(app_name).replace("-", " ").title().replace(" ", "")
        component_name = f"Eme{slug}" if not slug.startswith("Eme") else slug

        # 0. Load EME AI Guide for context
        guide_content = ""
        guide_path = os.path.join(settings.BASE_DIR, 'docs', 'EME_AI_GUIDE.md')
        if os.path.exists(guide_path):
            try:
                with open(guide_path, 'r', encoding='utf-8') as f:
                    guide_content = f.read()
            except:
                pass

        system_prompt = (
            "You are an expert Vue.js developer building a module for EME OS. "
            "Write exactly ONE valid Vue 3 Single File Component (.vue). Use standard HTML/CSS/JS with Composition API. "
            "Use Bootstrap 5 classes and EME-specific variables for styling. The root element MUST have the class 'eme-app-page'. "
            "Return ONLY the raw Vue code inside standard <template>, <script>, and <style> tags. "
            "Do NOT return markdown formatting like ```vue, just the raw code. Do NOT add any explanations.\n\n"
            f"REFERENCE GUIDE AND API:\n{guide_content}"
        )

        full_prompt = f"{system_prompt}\n\nTask: {prompt}"

        # Call Ollama
        try:
            # 1. Fetch available models first
            model_to_use = "qwen2.5-coder" # default desired
            try:
                tags_req = urllib.request.Request('http://localhost:11434/api/tags')
                with urllib.request.urlopen(tags_req, timeout=3) as tags_res:
                    tags_data = json.loads(tags_res.read().decode('utf-8'))
                    models = [m.get('name') for m in tags_data.get('models', [])]
                    
                    if models:
                        # Try to find best match
                        if not any(model_to_use in m for m in models):
                            # Fallback logic
                            for fallback in ["llama", "qwen", "mistral", "gemma", "phi"]:
                                match = next((m for m in models if fallback in m), None)
                                if match:
                                    model_to_use = match
                                    break
                            else:
                                model_to_use = models[-1] # Pick the last one if nothing matches
            except Exception as e:
                pass # Model fetch failed, will just try the default and fail gracefully
            
            # 2. Make the generation request
            req = urllib.request.Request(
                'http://localhost:11434/api/generate',
                data=json.dumps({
                    "model": model_to_use, 
                    "prompt": full_prompt,
                    "stream": False
                }).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                raw_code = result.get('response', '')
                
                # Cleanup potential markdown ticks if model ignores instructions
                if raw_code.startswith("```"):
                    raw_code = re.sub(r"^```(?:vue)?\n", "", raw_code)
                    raw_code = re.sub(r"\n```$", "", raw_code)
                
                draft = AIDraftApp.objects.create(
                    user=request.user,
                    name=app_name,
                    description=prompt[:200],
                    component_name=component_name,
                    vue_code=raw_code.strip()
                )
                
                return Response(AIDraftAppSerializer(draft).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Fallback to a different model if qwen fails
            return Response({'error': f'Помилка генерації (Ollama): {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

import os
from django.conf import settings

class AppPublishView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            draft = AIDraftApp.objects.get(pk=pk, user=request.user)
        except AIDraftApp.DoesNotExist:
            return Response({'error': 'Чернетку не знайдено'}, status=status.HTTP_404_NOT_FOUND)

        if draft.is_published:
            return Response({'error': 'Додаток вже опубліковано'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Write the .vue file
        component_file_name = f"{draft.component_name}.vue"
        file_path = os.path.join(settings.BASE_DIR, 'static', 'components', component_file_name)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(draft.vue_code)
        except Exception as e:
            return Response({'error': f'Помилка запису файлу: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 2. Update index.html to register the component
        index_path = os.path.join(settings.BASE_DIR, 'templates', 'index.html')
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find the components array. Example: const components = ['EmeAuthScreen', ...];
            # We'll use a regex to find the closing bracket of the array and insert our component
            import re
            
            # Simple check if it's already there
            if f"'{draft.component_name}'" not in content:
                # Find the last string in the array before "];"
                # This regex looks for the components array definition
                pattern = r"(const\s+components\s*=\s*\[[\s\S]*?)(\s*\];)"
                
                def replacement(match):
                    # match.group(1) is everything up to the last element
                    return f"{match.group(1)}, '{draft.component_name}'{match.group(2)}"
                
                new_content = re.sub(pattern, replacement, content, count=1)
                
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
        except Exception as e:
            return Response({'error': f'Помилка оновлення index.html: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3. Mark as published
        draft.is_published = True
        draft.save()

        return Response({'message': 'Додаток успішно опубліковано!'})

class AppDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            draft = AIDraftApp.objects.get(pk=pk, user=request.user)
        except AIDraftApp.DoesNotExist:
            return Response({'error': 'Додаток не знайдено'}, status=status.HTTP_404_NOT_FOUND)

        # 1. Delete the .vue file
        component_file_name = f"{draft.component_name}.vue"
        file_path = os.path.join(settings.BASE_DIR, 'static', 'components', component_file_name)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                return Response({'error': f'Помилка видалення файлу: {str(e)}'}, status=500)

        # 2. Optional: Remove from index.html registration?
        # For now, we'll keep it simple. The component just won't load if the file is missing.
        # But properly we should remove the string from components array.
        
        index_path = os.path.join(settings.BASE_DIR, 'templates', 'index.html')
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove from components array: 'EmeGeneratedStuff',
            import re
            pattern = re.compile(f"'{draft.component_name}',?\\s*")
            new_content = pattern.sub('', content)
            
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except:
            pass # Non-critical if index.html update fails

        # 3. Delete the draft record
        draft.delete()

        return Response({'message': 'Додаток успішно видалено!'})

class AppListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # 1. Hardcoded core apps (from EmeAppsStore.vue)
        core_apps = [
            {'id': 'park_adventures', 'category': 'games', 'name': 'Парк', 'icon': '🐉', 'color': '#4ca528', 'description': 'Інтерактивна гра з QR-сканером.', 'developer': 'EME Community'},
            {'id': 'qr_generator', 'category': 'utils', 'name': 'QR Генератор', 'icon': '🔍', 'color': '#00e5ff', 'description': 'Швидке створення QR-кодів.', 'developer': 'EME Utilities'},
            {'id': 'projects', 'category': 'productivity', 'name': 'Проєкти', 'icon': '📊', 'color': '#206bc4', 'description': 'Kanban дошки.', 'developer': 'EME Core'},
            {'id': 'chat', 'category': 'productivity', 'name': 'Чат', 'icon': '💬', 'color': '#00e5ff', 'description': 'Спілкування real-time.', 'developer': 'EME Core'},
            {'id': 'mafia', 'category': 'games', 'name': 'Мафія', 'icon': '🕵️‍♂️', 'color': '#dc3545', 'description': 'Психологічна гра.', 'developer': 'EME Community'},
            {'id': 'kb', 'category': 'productivity', 'name': 'База Знань', 'icon': '📚', 'color': '#f59f00', 'description': 'Нотатки та документація.', 'developer': 'EME Core'},
            {'id': 'ai_builder', 'category': 'productivity', 'name': 'AI App Builder', 'icon': '🪄', 'color': '#00e5ff', 'description': 'Створення додатків AI.', 'developer': 'EME Core'},
            {'id': 'gallery', 'category': 'media', 'name': 'Галерея', 'icon': '🖼️', 'color': '#e64980', 'description': 'Управління медіа.', 'developer': 'EME Core'},
            {'id': 'settings', 'category': 'system', 'name': 'Налаштування', 'icon': '⚙️', 'color': '#495057', 'description': 'Конфігурація системи.', 'developer': 'EME Core'},
            {'id': 'clone_master', 'category': 'system', 'name': 'Клон Мастер', 'icon': '📦', 'color': '#7048e8', 'description': 'Портативні клони.', 'developer': 'EME Core'},
            {'id': 'omni_tools', 'category': 'utils', 'name': 'OmniTools', 'icon': '🧰', 'color': '#ea868f', 'description': 'Інструменти розробника.', 'developer': 'EME Utilities'},
            {'id': 'microbin', 'category': 'utils', 'name': 'EME Pastebin', 'icon': '📋', 'color': '#206bc4', 'description': 'Обмін кодом.', 'developer': 'EME Utilities'},
            {'id': 'bookmarks', 'category': 'productivity', 'name': 'Закладки', 'icon': '🔖', 'color': '#f76707', 'description': 'Менеджер посилань.', 'developer': 'EME Utilities'},
            {'id': 'memos', 'category': 'productivity', 'name': 'Нотатки', 'icon': '📝', 'color': '#fcc419', 'description': 'Швидкі записи.', 'developer': 'EME Utilities'},
            {'id': 'sysmon', 'category': 'system', 'name': 'Системний Монітор', 'icon': '📈', 'color': '#0ca678', 'description': 'Ресурси сервера.', 'developer': 'EME Utilities'},
        ]

        # 2. Dynamically find published AI apps in static/components
        dynamic_apps = []
        components_dir = os.path.join(settings.BASE_DIR, 'static', 'components')
        if os.path.exists(components_dir):
            for filename in os.listdir(components_dir):
                if filename.startswith('EmeGenerated') and filename.endswith('.vue'):
                    component_name = filename[:-4]
                    # Find draft to get the original name
                    draft = AIDraftApp.objects.filter(component_name=component_name).first()
                    app_name = draft.name if draft else component_name.replace('EmeGenerated', '')
                    
                    dynamic_apps.append({
                        'id': component_name.lower().replace('eme', 'eme-'), # Map to component tag logic
                        'category': 'ai_apps',
                        'name': app_name,
                        'icon': '✨',
                        'color': '#6c00ff',
                        'description': 'AI генерував цей додаток.',
                        'developer': 'You & AI',
                        'component_name': component_name,
                        'draft_id': draft.id if draft else None
                    })

        return Response(core_apps + dynamic_apps)

class AppPreviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')
        name = request.data.get('name', 'PreviewComponent')
        
        if not code:
            return Response({'error': 'No code provided'}, status=400)
            
        # Write to EmePreview.vue
        preview_path = os.path.join(settings.BASE_DIR, 'static', 'components', 'EmePreview.vue')
        try:
            with open(preview_path, 'w', encoding='utf-8') as f:
                f.write(code)
            return Response({'success': True, 'component': 'EmePreview'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class AppGitPushView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            draft = AIDraftApp.objects.get(pk=pk, user=request.user)
        except AIDraftApp.DoesNotExist:
            return Response({'error': 'Додаток не знайдено'}, status=404)

        if not draft.is_published:
            return Response({'error': 'Додаток мусить бути опублікований перед пушем у Git'}, status=400)

        success, message = push_app_to_git(draft)
        if success:
            return Response({'message': message})
        else:
            return Response({'error': message}, status=500)

from .update_utils import download_and_update_from_zip

class GitAutoUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        settings_obj = CoreSettings.objects.filter(user=request.user).first()
        if not settings_obj or not settings_obj.auto_update:
            return Response({'error': 'Auto-Update вимкнено в налаштуваннях'}, status=400)

        # Try standard git pull first (works on desktop)
        success, out = auto_update_sync()
        if success:
            return Response({'message': 'Оновлення завершено через Git!', 'output': out})
        
        # If git pull fails (likely mobile or no .git), try ZIP update from GitHub
        repo_url = "https://github.com/Fil-m/eme.git" # TODO: get from settings
        success, out = download_and_update_from_zip(repo_url)
        
        if success:
            return Response({'message': 'Оновлення завершено через ZIP!', 'output': out})
        else:
            return Response({'error': f'Помилка оновлення: {out}'}, status=500)
