from django.conf import settings
from rest_framework import generics, permissions, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
import os
import json
import urllib.request
import re
from django.utils.text import slugify

from .models import CoreSettings, UserAppLayout, AIDraftApp
from .serializers import CoreSettingsSerializer, UserAppLayoutSerializer, AIDraftAppSerializer
from .git_utils import push_app_to_git, auto_update_sync
from .update_utils import download_and_update_from_zip

class CoreSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = CoreSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, created = CoreSettings.objects.get_or_create(user=self.request.user)
        return obj

class UserAppLayoutViewSet(viewsets.ModelViewSet):
    serializer_class = UserAppLayoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserAppLayout.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
        
        # Determine component name
        slug = slugify(app_name).replace("-", " ").title().replace(" ", "")
        component_name = f"Eme{slug}" if not slug.startswith("Eme") else slug

        if not prompt:
            # Manual creation mode
            draft = AIDraftApp.objects.create(
                user=request.user,
                name=app_name,
                description="Manual creation",
                component_name=component_name,
                vue_code='<template>\n  <div class="eme-app-page">\n    <h1>New App</h1>\n  </div>\n</template>\n\n<script setup>\n// Your code here\n</script>'
            )
            return Response(AIDraftAppSerializer(draft).data, status=status.HTTP_201_CREATED)

        # AI Generation Logic...
        guide_content = ""
        guide_path = os.path.join(settings.BASE_DIR, 'docs', 'EME_AI_GUIDE.md')
        if os.path.exists(guide_path):
            try:
                with open(guide_path, 'r', encoding='utf-8') as f:
                    guide_content = f.read()
            except: pass

        system_prompt = (
            "You are an expert Vue.js developer building a module for EME OS. "
            "Write exactly ONE valid Vue 3 Single File Component (.vue). Use standard HTML/CSS/JS with Composition API. "
            "Use Bootstrap 5 classes and EME-specific variables for styling. The root element MUST have the class 'eme-app-page'. "
            "Return ONLY the raw Vue code inside standard <template>, <script>, and <style> tags. "
            "Do NOT return markdown formatting like ```vue, just the raw code. Do NOT add any explanations.\n\n"
            f"REFERENCE GUIDE AND API:\n{guide_content}"
        )

        full_prompt = f"{system_prompt}\n\nTask: {prompt}"

        try:
            model_to_use = "qwen2.5-coder"
            # (Model discovery logic omitted for brevity or I could keep it, let's keep it simple for now)
            req = urllib.request.Request(
                'http://localhost:11434/api/generate',
                data=json.dumps({"model": model_to_use, "prompt": full_prompt, "stream": False}).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                raw_code = result.get('response', '')
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
            return Response({'error': f'Помилка генерації: {str(e)}'}, status=500)

class AppPublishView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            draft = AIDraftApp.objects.get(pk=pk, user=request.user)
        except AIDraftApp.DoesNotExist:
            return Response({'error': 'Чернетку не знайдено'}, status=404)

        if draft.is_published:
            return Response({'error': 'Додаток вже опубліковано'}, status=400)

        file_path = os.path.join(settings.BASE_DIR, 'static', 'components', f"{draft.component_name}.vue")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(draft.vue_code)
        except Exception as e:
            return Response({'error': f'Помилка запису файлу: {str(e)}'}, status=500)

        index_path = os.path.join(settings.BASE_DIR, 'templates', 'index.html')
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if f"'{draft.component_name}'" not in content:
                pattern = r"(const\s+components\s*=\s*\[[\s\S]*?)(\s*\];)"
                new_content = re.sub(pattern, lambda m: f"{m.group(1)}, '{draft.component_name}'{m.group(2)}", content, count=1)
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
        except Exception as e:
            return Response({'error': f'Помилка оновлення index.html: {str(e)}'}, status=500)

        draft.is_published = True
        draft.save()
        return Response({'message': 'Додаток успішно опубліковано!'})

class AppDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            draft = AIDraftApp.objects.get(pk=pk, user=request.user)
        except AIDraftApp.DoesNotExist:
            return Response({'error': 'Додаток не знайдено'}, status=404)

        file_path = os.path.join(settings.BASE_DIR, 'static', 'components', f"{draft.component_name}.vue")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except: pass

        index_path = os.path.join(settings.BASE_DIR, 'templates', 'index.html')
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            new_content = content.replace(f", '{draft.component_name}'", "").replace(f"'{draft.component_name}',", "")
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except: pass
            
        draft.delete()
        return Response({'message': 'Додаток успішно видалено!'})

class AppListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        core_apps = [
            {'id': 'park_adventures', 'category': 'games', 'name': 'Парк', 'icon': '🐉', 'color': '#4ca528', 'description': 'Інтерактивна гра.', 'developer': 'EME'},
            {'id': 'ai_builder', 'category': 'productivity', 'name': 'AI Builder', 'icon': '🪄', 'color': '#00e5ff', 'description': 'Створення додатків AI.', 'developer': 'EME'},
            {'id': 'settings', 'category': 'system', 'name': 'Налаштування', 'icon': '⚙️', 'color': '#495057', 'description': 'Конфігурація.', 'developer': 'EME'},
            {'id': 'kb', 'category': 'productivity', 'name': 'База Знань', 'icon': '📚', 'color': '#f59f00', 'description': 'Нотатки.', 'developer': 'EME'},
        ]
        
        dynamic_apps = []
        for draft in AIDraftApp.objects.filter(is_published=True):
            dynamic_apps.append({
                'id': draft.component_name,
                'category': 'ai_apps',
                'name': draft.name,
                'icon': '✨',
                'color': '#ff00d4',
                'description': draft.description,
                'developer': 'You & AI',
                'draft_id': draft.id
            })
            
        return Response(core_apps + dynamic_apps)

class AppPreviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')
        if not code: return Response({'error': 'No code'}, status=400)
        preview_path = os.path.join(settings.BASE_DIR, 'static', 'components', 'EmePreview.vue')
        with open(preview_path, 'w', encoding='utf-8') as f:
            f.write(code)
        return Response({'success': True, 'component': 'EmePreview'})

class AppGitPushView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            draft = AIDraftApp.objects.get(pk=pk, user=request.user)
        except AIDraftApp.DoesNotExist:
            return Response({'error': 'Додаток не знайдено'}, status=404)
        if not draft.is_published:
            return Response({'error': 'Спершу опублікуйте додаток'}, status=400)
        
        success, message = push_app_to_git(draft)
        if success: return Response({'message': message})
        else: return Response({'error': message}, status=500)

class GitAutoUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        settings_obj = CoreSettings.objects.filter(user=request.user).first()
        if not settings_obj or not settings_obj.auto_update:
            return Response({'error': 'Auto-Update вимкнено'}, status=400)
        
        success, out = auto_update_sync()
        if success: return Response({'message': 'Оновлено через Git!', 'output': out})
        
        success, out = download_and_update_from_zip("https://github.com/Fil-m/eme.git")
        if success: return Response({'message': 'Оновлено через ZIP!', 'output': out})
        else: return Response({'error': f'Помилка: {out}'}, status=500)
