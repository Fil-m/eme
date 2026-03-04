"""
Management command: python manage.py seed_projects
Seeds the 37 strategic projects from the master plan into the database
for the logged-in user (first admin user by default, or specify --username).

Usage:
  python manage.py seed_projects
  python manage.py seed_projects --username yourname
  python manage.py seed_projects --clear  # wipes existing and re-seeds
"""
from django.core.management.base import BaseCommand
from profiles.models import EMEUser
from projects.models import Project, ProjectAction
import datetime

SEED_DATA = [
    # (emoji, title, domain, status, priority, deadline, next_action)
    # ─── CRITICAL ───
    ('👶', 'Ксюша — підготовка до народження', 'life', 'this_week', 'critical', '2026-05-05', 'Erstausstattung, знайти акушерку, зібрати сумку'),
    ('⚖️', 'Батьківство (Vaterschaftsanerkennung)', 'life', 'this_week', 'critical', '2026-04-30', 'Записатись до Jugendamt Karlsruhe'),
    ('🧠', 'AuDHD Діагноз (Praxis121 / Jobcenter)', 'life', 'in_progress', 'critical', '2026-04-01', 'Подати Vermittlungsbudget в Jobcenter (~730€)'),
    ('💰', 'Spende 200€ зібрати (березень)', 'life', 'this_week', 'critical', '2026-03-31', 'Написати пости / звернутись до контактів'),
    # ─── STRATEGIC ───
    ('⚡', 'EME Core — стабілізація', 'eme', 'in_progress', 'high', None, 'Стабілізувати ядро перед новими модулями'),
    ('📋', 'EME Модуль Проектів (Kanban)', 'eme', 'done', 'high', None, 'Запустити, заповнити всі проекти'),
    ('🪴', 'Business Kindertreff', 'business', 'in_progress', 'high', '2026-04-15', 'Подати Einstiegsgeld в Jobcenter'),
    ('💼', 'Jobcenter подачі (Einstiegsgeld + Vermittlung)', 'life', 'this_week', 'high', '2026-03-10', 'Роздрукувати і здати обидва документи'),
    ('🔍', 'Пошук клієнтів (кімнати / події / соцмережі)', 'business', 'in_progress', 'high', None, 'Опублікувати оголошення, зв`язатись з кафе'),
    # ─── BUSINESS ───
    ('🖨️', 'Stina 3D Printing', 'business', 'this_week', 'high', None, 'Відправка цього тижня + інтерв`ю з волонтером'),
    ('🌿', 'Органайзери (лінійка для куріння)', 'business', 'in_progress', 'medium', None, 'Продовжити дизайн / прототипування'),
    ('🌱', 'Growboxes / Автоматичні теплиці', 'tech', 'in_progress', 'medium', None, 'Тестувати модульну систему'),
    ('📰', 'Мобільна друкарня з Андрюхою', 'business', 'backlog', 'medium', None, 'Узгодити концепцію і розподіл роботи'),
    ('🏃', 'Спортивний гурток (вулиця + походи)', 'community', 'backlog', 'medium', None, 'Зареєструвати групу, знайти походніка'),
    ('🔢', 'Акіра — ментальна арифметика', 'eme', 'backlog', 'low', None, 'UI в EME після стабілізації ядра'),
    ('🏠', 'Кімната для дітей Karlsruhe', 'business', 'in_progress', 'high', None, 'Знайти локацію / або почати вдома'),
    ('🎉', 'Події + Кейтерінг (батьки/діти)', 'business', 'backlog', 'medium', None, 'Знайти партнера по кейтерінгу'),
    ('☕', 'Я ГЕНАУ кафе — партнерство', 'business', 'in_progress', 'medium', None, 'Перший контакт про спільні події'),
    # ─── INFINITY BRAVES ───
    ('♾️', 'Infinity Braves — скринінг / діагностика', 'community', 'in_progress', 'medium', None, 'Розвивати платформу, більше юзерів'),
    ('♾️', 'Infinity Braves — зустрічі спільноти', 'community', 'backlog', 'medium', '2026-04-10', 'Запланувати першу зустріч'),
    ('♾️', 'Infinity Braves — документальний фільм', 'community', 'backlog', 'low', None, 'Написати сценарій / знайти оператора'),
    # ─── EME ECOSYSTEM ───
    ('⚡', 'EME P4P Bot', 'eme', 'done', 'medium', None, 'Підтримка'),
    ('💬', 'Mesh Chat (приватні + загальні чати)', 'eme', 'backlog', 'high', '2026-04-20', 'Реалізувати приватні чати'),
    ('📢', 'Дошка оголошень EME', 'eme', 'backlog', 'medium', None, 'Окремий застосунок'),
    ('🌐', 'Mesh Network P2P', 'eme', 'in_progress', 'high', None, 'Синхронізація між вузлами'),
    ('🤖', 'SMM Automation (виправити баги)', 'tech', 'frozen', 'low', None, 'Publishing flow зламаний'),
    ('🇩🇪', 'Deutsch Trainer', 'eme', 'backlog', 'low', None, 'UI після стабілізації ядра'),
    # ─── FROZEN / CONCEPTS ───
    ('🎮', 'Park Adventures — подія', 'community', 'this_week', 'high', '2026-03-10', 'Імплементувати прототип для події'),
    ('🎲', 'Gonka Connect (GPU partnership)', 'tech', 'frozen', 'low', None, 'Коли є GPU або партнерство'),
    ('🎨', 'Pixelchat', 'eme', 'frozen', 'low', None, 'Після Mesh Chat'),
    ('📖', 'Memology Universe (книга)', 'community', 'frozen', 'low', None, 'Довгостроковий проект'),
    ('🧶', '3D Printing Chainmail (хобі)', 'tech', 'frozen', 'low', None, 'Файли готові, за натхненням'),
    ('🇺🇦', 'Закордонний паспорт (моніторинг до 2028)', 'life', 'backlog', 'medium', '2028-01-01', 'Квартальний моніторинг варіантів'),
    ('🎬', 'Vlog Automator', 'tech', 'frozen', 'low', None, 'Коли є відео-контент'),
    ('📣', 'Ad Platform', 'business', 'frozen', 'low', None, 'Коли EME має більше юзерів'),
    ('🗺️', 'Drawing on Maps', 'eme', 'frozen', 'low', None, 'Коли є ресурс'),
    ('👧', 'Chat4Yasya', 'eme', 'frozen', 'low', None, 'Для Ксюші — через кілька років'),
]

ACTIONS = {
    'Ксюша — підготовка до народження': [
        'Подати Erstausstattung (до 20 тижня)',
        'Знайти акушерку (Hebamme)',
        'Bought: авто-крісло, матрас, ліжечко',
        'Зібрати Kliniktasche (35-36 тиждень)',
        'Підготувати документи для пологового',
    ],
    'Jobcenter подачі (Einstiegsgeld + Vermittlung)': [
        'Роздрукувати Businessplan (Kindertreff)',
        'Роздрукувати Antrag (Diagnose)',
        'Здати особисто або онлайн',
    ],
    'Стратегія — щотижневий ревю': [
        'Що зроблено за тиждень?',
        'Що ГОРИТЬ наступного тижня?',
        'Що можна заморозити?',
    ],
}


class Command(BaseCommand):
    help = 'Seeds 37 strategic projects into the database'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default=None)
        parser.add_argument('--clear', action='store_true', help='Delete existing projects first')

    def handle(self, *args, **options):
        username = options['username']
        if username:
            try:
                user = EMEUser.objects.get(username=username)
            except EMEUser.DoesNotExist:
                self.stderr.write(f'User "{username}" not found.')
                return
        else:
            user = EMEUser.objects.filter(is_superuser=True).first() or EMEUser.objects.first()

        if not user:
            self.stderr.write('No users found. Create at least one user first.')
            return

        if options['clear']:
            deleted, _ = Project.objects.filter(owner=user).delete()
            self.stdout.write(f'🧹 Cleared {deleted} existing projects.')

        created_count = 0
        for i, (emoji, title, domain, status, priority, deadline, next_action) in enumerate(SEED_DATA):
            deadline_date = datetime.date.fromisoformat(deadline) if deadline else None
            p, created = Project.objects.get_or_create(
                owner=user, title=title,
                defaults={
                    'emoji': emoji,
                    'domain': domain,
                    'status': status,
                    'priority': priority,
                    'deadline': deadline_date,
                    'next_action': next_action,
                    'order': i,
                }
            )
            if created:
                created_count += 1
                actions = ACTIONS.get(title, [])
                for action_text in actions:
                    ProjectAction.objects.create(project=p, text=action_text)

        self.stdout.write(self.style.SUCCESS(
            f'OK: Created {created_count}/{len(SEED_DATA)} projects for user "{user.username}"'
        ))
