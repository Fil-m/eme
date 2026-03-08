from django.conf import settings
from rest_framework import generics, permissions
from .models import CoreSettings
from .serializers import CoreSettingsSerializer

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
