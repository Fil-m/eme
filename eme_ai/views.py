"""
EME AI Module — Main Views

GET  /api/ai/providers/       — list available providers + models
POST /api/ai/scaffold/        — generate plan (no save)
POST /api/ai/scaffold/apply/  — generate + save to DB
"""
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from .registry import get_provider, all_providers
from .models import AIRequest


# ── Scaffolder router ─────────────────────────────────────────
def get_scaffolder(module: str):
    if module == 'projects':
        from .scaffolders.projects import ProjectScaffolder
        return ProjectScaffolder()
    raise ValueError(f"Unknown scaffold module: '{module}'")


# ── Views ─────────────────────────────────────────────────────

class ProviderListView(APIView):
    """GET /api/ai/providers/ — list providers with online status and models."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(all_providers())


class ScaffoldView(APIView):
    """POST /api/ai/scaffold/ — generate a plan, don't save."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        module = request.data.get('module', 'projects')
        provider_name = request.data.get('provider', 'ollama')
        model = request.data.get('model', 'llama3')
        context = request.data.get('context', {})

        log = AIRequest(
            user=request.user,
            module=module,
            provider=provider_name,
            model=model,
        )

        try:
            scaffolder = get_scaffolder(module)
            provider = get_provider(provider_name)
            prompt = scaffolder.build_prompt(context)
            log.prompt_preview = prompt[:497] + '...' if len(prompt) > 500 else prompt

            raw = provider.generate(prompt, model=model)
            plan = scaffolder.parse_response(raw)

            log.status = 'ok'
            log.save()
            return Response({'plan': plan, 'provider': provider_name, 'model': model})

        except requests.ConnectionError:
            log.status = 'error'
            log.error_msg = 'Provider offline'
            log.save()
            return Response(
                {'error': f'{provider_name} is not reachable. Is it running?'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except requests.Timeout:
            log.status = 'timeout'
            log.save()
            return Response({'error': 'AI request timed out'}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except Exception as e:
            log.status = 'error'
            log.error_msg = str(e)[:500]
            log.save()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScaffoldApplyView(APIView):
    """POST /api/ai/scaffold/apply/ — generate plan AND save it to DB."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        module = request.data.get('module', 'projects')
        provider_name = request.data.get('provider', 'ollama')
        model = request.data.get('model', 'llama3')
        context = request.data.get('context', {})

        # Ensure user owns the target object for security
        if module == 'projects':
            from projects.models import Project
            pid = context.get('project_id')
            if not pid or not Project.objects.filter(pk=pid, owner=request.user).exists():
                return Response({'error': 'Project not found or access denied.'}, status=403)

        log = AIRequest(user=request.user, module=module, provider=provider_name, model=model)

        try:
            scaffolder = get_scaffolder(module)
            provider = get_provider(provider_name)
            prompt = scaffolder.build_prompt(context)
            log.prompt_preview = prompt[:497] + '...' if len(prompt) > 500 else prompt

            raw = provider.generate(prompt, model=model)
            plan = scaffolder.parse_response(raw)
            result = scaffolder.apply(plan, context)

            log.status = 'ok'
            log.save()
            return Response({'applied': result, 'plan': plan, 'provider': provider_name})

        except requests.ConnectionError:
            log.status = 'error'; log.error_msg = 'offline'; log.save()
            return Response({'error': f'{provider_name} is offline.'}, status=503)
        except requests.Timeout:
            log.status = 'timeout'; log.save()
            return Response({'error': 'AI request timed out.'}, status=504)
        except Exception as e:
            log.status = 'error'; log.error_msg = str(e)[:500]; log.save()
            return Response({'error': str(e)}, status=500)
