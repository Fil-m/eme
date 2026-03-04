"""
Ollama AI proxy for project planning.
POST /api/projects/ai/plan/

Requires Ollama running at localhost:11434.
Install: https://ollama.com — then: ollama pull llama3
"""
import json
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from .models import Project

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3"

SYSTEM_PROMPT = """You are EME AI Project Planner. 
Given a project title and description, return ONLY valid JSON (no commentary, no markdown) in this exact format:
{
  "roles": [
    {"name": "Role Name", "emoji": "🧑", "description": "Short role description"}
  ],
  "actions": [
    {"text": "Action text", "priority": "high", "role_name": "Role Name", "depends_on_index": null}
  ]
}

Rules:
- 2-5 roles max, 5-10 actions max
- priority: critical | high | medium | low
- depends_on_index: null or 0-based index of action this one depends on
- Keep everything concise and practical
- Respond ONLY with the JSON object, nothing else
"""


class AIProjectPlanView(APIView):
    """POST /api/projects/ai/plan/ — generate roles + actions via Ollama"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        project_id = request.data.get('project_id')
        user_prompt = request.data.get('prompt', '')
        model = request.data.get('model', DEFAULT_MODEL)

        # Build context from project if provided
        context = ''
        if project_id:
            try:
                project = Project.objects.get(pk=project_id, owner=request.user)
                context = f'Project: "{project.emoji} {project.title}"\n'
                if project.description:
                    context += f'Description: {project.description}\n'
                context += f'Domain: {project.domain}\n'
            except Project.DoesNotExist:
                pass

        if not context and not user_prompt:
            return Response({'error': 'Provide project_id or prompt'}, status=400)

        full_prompt = SYSTEM_PROMPT + "\n\n" + context
        if user_prompt:
            full_prompt += f"\nUser request: {user_prompt}"

        # Call Ollama
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    'model': model,
                    'prompt': full_prompt,
                    'stream': False,
                    'options': {'temperature': 0.3, 'num_predict': 1024}
                },
                timeout=60
            )
            resp.raise_for_status()
            raw = resp.json().get('response', '')

            # Parse JSON from response
            parsed = self._extract_json(raw)
            if parsed is None:
                return Response({'error': 'AI returned invalid JSON', 'raw': raw[:500]}, status=502)

            return Response({'plan': parsed, 'model': model})

        except requests.ConnectionError:
            return Response(
                {'error': 'Ollama not running. Start it with: ollama serve (requires Ollama installed)'},
                status=503
            )
        except requests.Timeout:
            return Response({'error': 'Ollama timeout (>60s). Try a smaller model.'}, status=504)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def _extract_json(self, text):
        """Extract JSON object from text, even if model adds extra words."""
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Try to find JSON block
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        return None


class OllamaModelsView(APIView):
    """GET /api/projects/ai/models/ — list available Ollama models"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            resp = requests.get('http://localhost:11434/api/tags', timeout=5)
            resp.raise_for_status()
            models = [m['name'] for m in resp.json().get('models', [])]
            return Response({'models': models, 'online': True})
        except Exception:
            return Response({'models': [], 'online': False,
                             'hint': 'Run: ollama serve'})
