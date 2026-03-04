"""
Management command: python manage.py sync_calendar_deadlines

Syncs projects with deadlines → Google Calendar events.

Requirements:
  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

Setup (one-time):
  1. Go to console.cloud.google.com → Enable Calendar API
  2. Create OAuth 2.0 Desktop credentials → Download as credentials.json
  3. Place credentials.json in the same dir as manage.py (d:/dev/eme/)
  4. First run will open browser for authorization → saves token.json

Usage:
  python manage.py sync_calendar_deadlines
  python manage.py sync_calendar_deadlines --dry-run
  python manage.py sync_calendar_deadlines --username robosapiens
  python manage.py sync_calendar_deadlines --clear-all
"""
import os
import json
import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

CREDENTIALS_FILE = os.path.join(settings.BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(settings.BASE_DIR, 'token.json')

SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = 'primary'  # or paste the ID of a specific calendar
EVENT_TAG = '[EME]'       # prefix added to event summaries for identification


class Command(BaseCommand):
    help = 'Sync project deadlines to Google Calendar'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be synced without creating events')
        parser.add_argument('--username', type=str, default=None, help='Username to sync projects for (default: first superuser)')
        parser.add_argument('--clear-all', action='store_true', help='Delete all [EME] events from calendar before syncing')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        username = options['username']
        clear_all = options['clear_all']

        # ── Build project list ────────────────────────────────────────────────
        from profiles.models import EMEUser
        from projects.models import Project

        if username:
            try:
                user = EMEUser.objects.get(username=username)
            except EMEUser.DoesNotExist:
                self.stderr.write(f'User "{username}" not found.')
                return
        else:
            user = EMEUser.objects.filter(is_superuser=True).order_by('id').first()
            if not user:
                user = EMEUser.objects.order_by('id').first()

        if not user:
            self.stderr.write('No users found in the database.')
            return

        projects = Project.objects.filter(
            owner=user,
            deadline__isnull=False,
        ).exclude(status__in=['done', 'frozen']).order_by('deadline')

        self.stdout.write(f'User: {user.username} | Projects with deadlines: {projects.count()}')

        if dry_run:
            self.stdout.write('\n--- DRY RUN (no events will be created) ---\n')
            for p in projects:
                self.stdout.write(
                    f'  [{p.priority.upper():8}] {p.emoji} {p.title} → {p.deadline} [{p.status}]'
                )
            self.stdout.write(f'\n{projects.count()} events would be synced.')
            return

        # ── Google Calendar auth ──────────────────────────────────────────────
        service = self._get_calendar_service()
        if not service:
            return

        # ── Clear existing EME events ─────────────────────────────────────────
        if clear_all:
            self._clear_eme_events(service)

        # ── Sync each project ─────────────────────────────────────────────────
        synced = 0
        skipped = 0

        for p in projects:
            deadline_str = p.deadline.isoformat() if hasattr(p.deadline, 'isoformat') else str(p.deadline)
            summary = f'{EVENT_TAG} {p.emoji} {p.title}'
            description = self._build_description(p)

            # Check if event already exists (by summary + date)
            existing = self._find_event(service, summary, deadline_str)
            if existing:
                # Update description if needed
                service.events().patch(
                    calendarId=CALENDAR_ID,
                    eventId=existing['id'],
                    body={'description': description}
                ).execute()
                skipped += 1
                self.stdout.write(f'  ~ Updated: {summary[:50]}')
            else:
                event = {
                    'summary': summary,
                    'description': description,
                    'start': {'date': deadline_str},
                    'end': {'date': deadline_str},
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': 24 * 60},   # 1 day before
                            {'method': 'popup', 'minutes': 3 * 60},    # 3 hours before
                        ]
                    },
                    'colorId': self._priority_color_id(p.priority),
                }
                service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
                synced += 1
                self.stdout.write(f'  + Created: {summary[:50]} ({deadline_str})')

        self.stdout.write(f'\nOK: {synced} created, {skipped} updated.')

    def _build_description(self, project):
        lines = []
        if project.description:
            lines.append(project.description)
        if project.next_action:
            lines.append(f'Next: {project.next_action}')
        lines.append(f'Domain: {project.domain} | Priority: {project.priority} | Status: {project.status}')
        if project.actions.exists():
            done = project.actions.filter(is_done=True).count()
            total = project.actions.count()
            lines.append(f'Actions: {done}/{total} done')
        return '\n'.join(lines)

    def _priority_color_id(self, priority):
        """Google Calendar color IDs: 11=tomato, 5=banana, 2=sage, 8=graphite"""
        return {'critical': '11', 'high': '5', 'medium': '2', 'low': '8'}.get(priority, '2')

    def _find_event(self, service, summary, date_str):
        result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=f'{date_str}T00:00:00Z',
            timeMax=f'{date_str}T23:59:59Z',
            q=EVENT_TAG,
            singleEvents=True,
        ).execute()
        for event in result.get('items', []):
            if event.get('summary', '') == summary:
                return event
        return None

    def _clear_eme_events(self, service):
        self.stdout.write('Clearing existing [EME] events...')
        page_token = None
        deleted = 0
        while True:
            result = service.events().list(
                calendarId=CALENDAR_ID,
                q=EVENT_TAG,
                pageToken=page_token,
                singleEvents=True,
            ).execute()
            for event in result.get('items', []):
                if EVENT_TAG in event.get('summary', ''):
                    service.events().delete(calendarId=CALENDAR_ID, eventId=event['id']).execute()
                    deleted += 1
            page_token = result.get('nextPageToken')
            if not page_token:
                break
        self.stdout.write(f'Deleted {deleted} [EME] events.')

    def _get_calendar_service(self):
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            self.stderr.write(
                'ERROR: Google API libraries not installed.\n'
                'Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client'
            )
            return None

        if not os.path.exists(CREDENTIALS_FILE):
            self.stderr.write(
                f'ERROR: credentials.json not found at {CREDENTIALS_FILE}\n'
                '1. Go to console.cloud.google.com\n'
                '2. Enable Calendar API\n'
                '3. Create OAuth 2.0 Desktop credentials\n'
                '4. Download JSON → save as credentials.json next to manage.py'
            )
            return None

        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())

        return build('calendar', 'v3', credentials=creds)
