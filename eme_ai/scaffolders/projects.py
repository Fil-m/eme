"""
Project scaffolder — generates roles + actions for a given project.
Called by ScaffoldApplyView and also by the plan-only endpoint.
"""
import json
from .base import BaseScaffolder


SYSTEM_PROMPT = """\
You are EME Project Planner AI. Given a project description and team size, \
return ONLY valid JSON (no markdown, no commentary) in this exact format:

{
  "roles": [
    {"name": "Role Name", "emoji": "🧑", "description": "What this role does"}
  ],
  "actions": [
    {
      "text": "Concrete action step",
      "priority": "high",
      "role_name": "Role Name or null",
      "deadline_days": 3,
      "status": "todo"
    }
  ]
}

Rules:
- Create 2–5 roles relevant to this project
- Create 5–15 concrete action steps
- priority: critical | high | medium | low
- deadline_days: integer days from today (null if no deadline makes sense)
- status: todo | doing | done
- role_name: must match one of the role names you defined, or null
- Be practical and specific to the project description
- CRITICAL: Write all role names, actions, and descriptions in the EXACT SAME LANGUAGE as the project description and title.
- Respond ONLY with the JSON object
"""


class ProjectScaffolder(BaseScaffolder):
    module = 'projects'

    def build_prompt(self, context: dict) -> str:
        title = context.get('title', '')
        description = context.get('description', '')
        team_size = context.get('team_size', 1)
        domain = context.get('domain', '')

        return (
            SYSTEM_PROMPT
            + f"\n\nProject: {title}"
            + (f"\nDescription: {description}" if description else "")
            + (f"\nDomain: {domain}" if domain else "")
            + f"\nEstimated team size: {team_size} people"
            + "\n\nGenerate the JSON plan now:"
        )

    def parse_response(self, raw: str) -> dict:
        """Extract and validate JSON from AI response."""
        raw = raw.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Try to find JSON block if model added extra text
        start, end = raw.find('{'), raw.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass
        raise ValueError(f"AI returned invalid JSON. Raw: {raw[:300]}")

    def apply(self, plan: dict, context: dict) -> dict:
        """Save roles and actions to the project DB. Returns summary."""
        from datetime import date, timedelta
        from projects.models import ProjectRole, ProjectAction, Project
        
        # --- Language Translation Phase ---
        try:
            from deep_translator import GoogleTranslator
            from langdetect import detect
            
            title = context.get('title', '')
            desc = context.get('description', '')
            text_to_detect = f"{title} {desc}".strip()
            
            target_lang = 'uk'
            if len(text_to_detect) >= 3:
                try:
                    target_lang = detect(text_to_detect)
                except Exception:
                    pass
                    
            translator = GoogleTranslator(source='auto', target=target_lang)
            
            def safe_translate(txt: str) -> str:
                if not txt: return txt
                try:
                    res = translator.translate(txt)
                    return res if res else txt
                except Exception as e:
                    print("Translate err:", e)
                    return txt

            for r in plan.get('roles', []):
                if r.get('name'): r['name'] = safe_translate(r['name'])
                if r.get('description'): r['description'] = safe_translate(r['description'])
            for a in plan.get('actions', []):
                if a.get('text'): a['text'] = safe_translate(a['text'])
                if a.get('role_name'): a['role_name'] = safe_translate(a['role_name'])
        except ImportError:
            pass # Translation disabled if libs missing
        # ----------------------------------

        project_id = context.get('project_id')
        if not project_id:
            raise ValueError("project_id required in context for apply()")

        project = Project.objects.get(pk=project_id)

        roles_created = []
        role_map = {}  # name → ProjectRole instance

        for r in plan.get('roles', []):
            name = r.get('name', '').strip()
            if not name:
                continue
            role, _ = ProjectRole.objects.get_or_create(
                project=project,
                name=name,
                defaults={
                    'emoji': r.get('emoji', '👤'),
                    'description': r.get('description', ''),
                }
            )
            roles_created.append(name)
            role_map[name] = role

        actions_created = []
        today = date.today()

        for a in plan.get('actions', []):
            text = a.get('text', '').strip()
            if not text:
                continue
            role_name = a.get('role_name')
            assignee_role = role_map.get(role_name) if role_name else None
            deadline_days = a.get('deadline_days')
            deadline = today + timedelta(days=int(deadline_days)) if deadline_days else None

            ProjectAction.objects.create(
                project=project,
                text=text,
                priority=a.get('priority', 'medium'),
                status=a.get('status', 'todo'),
                deadline=deadline,
                assignee_role=assignee_role,
            )
            actions_created.append(text[:60])

        return {
            'roles': roles_created,
            'actions_count': len(actions_created),
        }
