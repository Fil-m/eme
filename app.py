import os
import json
import uuid
import socket
from datetime import datetime, timedelta
import requests
import zipfile
import io
import threading
import time
import qrcode
from flask import Flask, render_template, request, redirect, session, jsonify, make_response, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from knowledge_base import KNOWLEDGE_BASE

app = Flask(__name__)
app.secret_key = "eme-secret-key-change-in-prod"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///eme.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

db = SQLAlchemy(app)

# --- MODELS ---

class Node(db.Model):
    __tablename__ = 'nodes'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

class ActionType(db.Model):
    __tablename__ = 'action_types'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False) # e.g., "Help", "Onboarding"
    description = db.Column(db.Text, nullable=True)
    schema = db.Column(db.Text, nullable=False) # JSON string defining fields
    creator_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=True)
    parent_type_id = db.Column(db.String(36), db.ForeignKey('action_types.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('Node', backref='created_types', foreign_keys=[creator_id])
    parent = db.relationship('ActionType', remote_side=[id], backref='children')

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.String(36), db.ForeignKey('action_types.id'), nullable=True)
    creator_node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=False)
    parent_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=True)
    status = db.Column(db.String(20), default='active') # active, proposed, completed, archived
    definition_of_done = db.Column(db.Text, nullable=True) # JSON/Text requirements
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('Node', backref='created_projects')
    category = db.relationship('ActionType', backref='projects')
    parent = db.relationship('Project', remote_side=[id], backref='subprojects')

class Milestone(db.Model):
    __tablename__ = 'milestones'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='active') # active, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='milestones')

class Participation(db.Model):
    __tablename__ = 'participations'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=False)
    role = db.Column(db.String(20), default='member') # owner, member, witness
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='participants')
    node = db.relationship('Node', backref='project_participations')

class Action(db.Model):
    __tablename__ = 'actions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action_type_id = db.Column(db.String(36), db.ForeignKey('action_types.id'), nullable=False)
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=False) # Creator
    assignee_node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=True)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=True)
    milestone_id = db.Column(db.String(36), db.ForeignKey('milestones.id'), nullable=True)
    
    payload = db.Column(db.Text, nullable=False) # JSON with actual data
    status = db.Column(db.String(20), default='proposed') # proposed, in_progress, completed, verified
    
    required_witnesses = db.Column(db.Integer, default=1)
    allowed_witnesses = db.Column(db.Text, nullable=True) # JSON list of node IDs or null for anyone
    witnesses_data = db.Column(db.Text, nullable=True) # JSON list of nodes who verified
    
    evidence_photo = db.Column(db.Text, nullable=True) # Base64 or path
    keep_evidence = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    node = db.relationship('Node', backref='actions_created', foreign_keys=[node_id])
    assignee = db.relationship('Node', backref='actions_assigned', foreign_keys=[assignee_node_id])
    action_type = db.relationship('ActionType', backref='actions')
    project = db.relationship('Project', backref='actions')
    milestone = db.relationship('Milestone', backref='actions')

class Peer(db.Model):
    __tablename__ = 'peers'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address = db.Column(db.String(100), unique=True, nullable=False)
    last_success = db.Column(db.DateTime, nullable=True)
    failure_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- HELPERS ---

app.jinja_env.filters['from_json'] = lambda s: json.loads(s) if s else {}

def migrate_db_schema():
    """Simple migration helper to add missing columns to existing tables."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    
    # Tables and columns that might be missing in older DB versions
    needed_columns = {
        'actions': [
            ('milestone_id', 'VARCHAR(36)'),
            ('assignee_node_id', 'VARCHAR(36)'),
            ('project_id', 'VARCHAR(36)'),
            ('evidence_photo', 'TEXT'),
            ('keep_evidence', 'BOOLEAN DEFAULT 0'),
            ('updated_at', 'DATETIME')
        ],
        'projects': [
            ('parent_id', 'VARCHAR(36)'),
            ('status', 'VARCHAR(20) DEFAULT "active"'),
            ('definition_of_done', 'TEXT')
        ]
    }
    
    for table_name, new_cols in needed_columns.items():
        try:
            # SQLite specific column check using raw SQL for maximum reliability
            with db.engine.connect() as conn:
                res = conn.execute(text(f"PRAGMA table_info({table_name})"))
                existing_cols = [row[1] for row in res.fetchall()]
            
            if not existing_cols:
                # Table might not exist yet, create_all will handle it
                continue
                
            for col_name, col_type in new_cols:
                if col_name not in existing_cols:
                    try:
                        with db.engine.begin() as conn:
                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                        msg = f"!!! Migration SUCCESS: Added column {col_name} to {table_name}"
                        print(msg)
                        app.logger.info(msg)
                    except Exception as e:
                        msg = f"!!! Migration Warning: Could not add {col_name} to {table_name}: {e}"
                        print(msg)
                        app.logger.warning(msg)
        except Exception as e:
            print(f"!!! Migration Error on table {table_name}: {e}")

def get_current_node():
    node_id = session.get("node_id")
    if node_id:
        return Node.query.get(node_id)
    return None

def get_or_create_node_from_cookie():
    device_id = request.cookies.get("device_id")
    if not device_id:
        return None, None
    
    node = Node.query.filter_by(device_id=device_id).first()
    if not node:
        # Auto-register new node if device_id exists in cookie but not in DB (rare case, or sync issue)
        # However, usually we create both.
        # But if we are here, it means cookie exists. Let's trust it for now or create new node.
        pass 
    return node, device_id

def get_local_ip():
    """Returns the local IP address using multiple strategies for robustness."""
    # Strategy 1: External socket (works if internet or gateway is Up)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if not ip.startswith("127."): return ip
    except:
        pass

    # Strategy 2: Internal broadcast (works offline in many LANs)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        if not ip.startswith("127."): return ip
    except:
        pass

    # Strategy 3: Hostname enumeration
    try:
        hostname = socket.gethostname()
        ips = socket.gethostbyname_ex(hostname)[2]
        for ip in ips:
            if not ip.startswith("127."): return ip
    except:
        pass

    return "127.0.0.1"

# --- MIDDLEWARE ---

@app.before_request
def identify_node():
    if request.endpoint in ("static", "sync_export_api"):
        return

    device_id = request.cookies.get("device_id")
    if device_id:
        node = Node.query.filter_by(device_id=device_id).first()
        if node:
            session["node_id"] = node.id
            node.last_seen = datetime.utcnow()
            db.session.commit()
    
    # If no cookie, we wait until a view logic handles it or we redirect to a setup/welcome if needed
    # But for now, we'll handle creation in the 'index' or specific routes if missing.

# --- ROUTES ---

@app.route("/")
def index():
    node = get_current_node()
    if not node:
        # First time visitor logic
        new_device_id = str(uuid.uuid4())
        new_node = Node(device_id=new_device_id, name="New Node")
        db.session.add(new_node)
        db.session.commit()
        
        session["node_id"] = new_node.id
        resp = make_response(redirect("/who"))
        resp.set_cookie("device_id", new_device_id, max_age=60*60*24*365*10)
        return resp

    # Fetch recent actions with joined models for efficiency
    actions = Action.query.options(joinedload(Action.node), joinedload(Action.action_type)).order_by(Action.created_at.desc()).limit(50).all()
    
    # Parse payloads for display
    display_actions = []
    for a in actions:
        try:
            data = json.loads(a.payload)
        except:
            data = {}
            
        display_actions.append({
            "id": a.id,
            "who": a.node.name or "Anonymous",
            "type": a.action_type.name,
            "data": data,
            "when": a.created_at.strftime("%Y-%m-%d %H:%M"),
            "color": _get_type_color(a.action_type.name),
            "status": a.status,
            "assignee": a.assignee.name if a.assignee else None,
            "project": a.project.name if a.project else None,
            "creator_id": a.node.id
        })

    # Projects for sidebar
    active_projects = Project.query.filter_by(status='active').all()

    return render_template("index.html", actions=display_actions, current_node=node, projects=active_projects)

@app.route("/report/<node_id>")
def generate_report(node_id):
    # Mini-resume logic
    target_node = Node.query.get_or_404(node_id)
    actions = Action.query.filter_by(assignee_node_id=target_node.id, status='verified').all()
    
    # Simple aggregation by category
    stats = {}
    for a in actions:
        cat = a.action_type.name
        stats[cat] = stats.get(cat, 0) + 1
        
    return render_template("report.html", node=target_node, stats=stats)

# --- INTERNATIONALIZATION (Offline) ---
TRANSLATIONS = {
    "uk": {
        "nav_home": "Головна",
        "nav_knowledge": "База знань",
        "nav_types": "Типи",
        "nav_stats": "Статистика",
        "nav_sync": "SYNC",
        "nav_repl": "Нова нода",
        "nav_home_short": "Дім",
        "nav_projects_short": "Проекти",
        "nav_sync_short": "Синх",
        "nav_cabinet_short": "Кабінет",
        "footer_text": "EME v0.1 • Вузол",
        "guest": "Гість",
        "lang_switch": "EN",
        "actions_title": "Індекс Дій",
        "btn_add_action": "Додати дію",
        "btn_filter": "Фільтр",
        "placeholder_search": "Пошук...",
        "no_actions": "Поки що немає записів.",
        "read_back": "До списку",
        "read_updated": "Оновлено",
        "install_title": "Стати Вузлом",
        "install_desc": "Завантажте та запустіть свій власний вузол EME.",
        "termux_instr": "Інструкція Termux (Android)",
        "win_instr": "Windows / Linux",
        "read_knowledge_desc": "ДНК нашої мережі. Ці документи синхронізуються між усіма вузлами.",
        "sync_title": "Синхронізація (Mesh)",
        "sync_my_addr": "Твоя адреса",
        "sync_scan_qr": "Скануй для підключення",
        "sync_pull_title": "Підтягнути дані",
        "sync_enter_addr": "Введіть адресу друга (наприклад: http://...)",
        "sync_btn": "Запустити Sync",
        "sync_how_title": "Як це працює?",
        "sync_how_desc": "Всі дії мають унікальні ID. Sync забирає нові дані але не створює дублікатів.",
        "qr_install_label": "Або скануй щоб встановити термінал:",
        "scan_btn": "Сканувати QR",
        "stop_scan_btn": "Зупинити",
        "cam_error": "Помилка камери. Перевірте дозволи або спробуйте на localhost/HTTPS.",
        "who_title": "Хто ти?",
        "who_desc": "Це імʼя буде видно біля кожної твоєї дії.",
        "who_label_name": "Твоє імʼя або псевдо",
        "who_placeholder_name": "Наприклад: Тарас",
        "who_label_device_id": "ID пристрою (автоматичний)",
        "who_btn_save": "Зберегти",
        "who_stats_title": "Твій внесок",
        "who_stats_actions": "Дій зафіксовано",
        "who_stats_types": "Типів створено",
        "types_title": "Типи дій",
        "types_desc": "Обери тип, щоб додати дію, або створи новий.",
        "types_create_title": "Створити новий ген (тип)",
        "types_placeholder_name": "Назва (напр. Волонтерство)",
        "types_placeholder_desc": "Короткий опис",
        "types_setup_fields": "Налаштувати поля (JSON)",
        "types_fields_desc": "Залиште пустим для стандарту (Кому, Що).",
        "types_schema_recipient": "Кому",
        "types_schema_details": "Деталі",
        "types_btn_create": "Створити Тип",
        "stats_title": "Пульс мережі",
        "stats_table_type": "Тип",
        "stats_table_count": "Дій",
        "nav_workspace_label": "Простір",
        "nav_network_label": "Мережа",
        "nav_cabinet": "Кабінет",
        "nav_projects": "Проекти",
        "nav_who": "Хто я",
        "cabinet_title": "Мій Кабінет",
        "cabinet_desc": "Твій особистий простір для фокусу та результатів.",
        "cabinet_tasks_active": "завдань в роботі",
        "cabinet_my_tasks": "Мої завдання",
        "cabinet_to_verify": "Очікують верифікації",
        "projects_title": "Проекти",
        "projects_create_btn": "Створити проект",
        "projects_new_title": "Новий проект",
        "projects_placeholder_name": "Назва проекту",
        "projects_placeholder_desc": "Опис проекту",
        "projects_parent_label": "Батьківський проект (Папка):",
        "projects_root_option": "-- Без папки (Корінь) --",
        "projects_empty": "Проектів поки немає. Створіть перший!",
        "projects_nested_actions": "Вкладених дій",
    },
    "en": {
        "nav_home": "Home",
        "nav_knowledge": "Knowledge",
        "nav_stats": "Stats",
        "nav_who": "Who am I",
        "nav_home_short": "Home",
        "nav_projects_short": "Projects",
        "nav_sync_short": "Sync",
        "nav_cabinet_short": "Cabinet",
        "lang_switch": "Українська",
        "nav_types": "Types",
        "nav_sync": "SYNC",
        "nav_repl": "Node+",
        "footer_text": "EME v0.1 • Node",
        "guest": "Guest",
        "actions_title": "Action Index",
        "btn_add_action": "Add Action",
        "btn_filter": "Filter",
        "placeholder_search": "Search...",
        "no_actions": "No records yet.",
        "read_back": "Back to list",
        "read_updated": "Updated",
        "install_title": "Become a Node",
        "install_desc": "Download and run your own EME node.",
        "termux_instr": "Termux Instructions (Android)",
        "win_instr": "Windows / Linux",
        "read_knowledge_desc": "The DNA of our network. These documents sync across all nodes.",
        "sync_title": "Synchronization (Mesh)",
        "sync_my_addr": "Your Address",
        "sync_scan_qr": "Scan to connect",
        "sync_pull_title": "Pull Data",
        "sync_enter_addr": "Enter friend's address (e.g. http://...)",
        "sync_btn": "Run Sync",
        "sync_how_title": "How it works?",
        "sync_how_desc": "All actions have unique IDs. Sync pulls new data without duplicates.",
        "qr_install_label": "Or scan to install terminal:",
        "scan_btn": "Scan QR",
        "stop_scan_btn": "Stop",
        "cam_error": "Camera error. Check permissions or try localhost/HTTPS.",
        "who_title": "Who are you?",
        "who_desc": "This name will be visible next to each of your actions.",
        "who_label_name": "Your name or alias",
        "who_placeholder_name": "Example: Taras",
        "who_label_device_id": "Device ID (automatic)",
        "who_btn_save": "Save",
        "who_stats_title": "Your contribution",
        "who_stats_actions": "Actions recorded",
        "who_stats_types": "Types created",
        "types_title": "Action Types",
        "types_desc": "Choose a type to add an action, or create a new one.",
        "types_create_title": "Create new gene (type)",
        "types_placeholder_name": "Name (e.g. Volunteering)",
        "types_placeholder_desc": "Short description",
        "types_setup_fields": "Configure fields (JSON)",
        "types_fields_desc": "Leave empty for standard (To whom, Details).",
        "types_schema_recipient": "Recipient",
        "types_schema_details": "Details",
        "types_btn_create": "Create Type",
        "stats_title": "Network Pulse",
        "stats_table_type": "Type",
        "stats_table_count": "Actions",
        "nav_workspace_label": "Workspace",
        "nav_network_label": "Network",
        "nav_cabinet": "Cabinet",
        "nav_projects": "Projects",
        "nav_who": "Who I am",
        "cabinet_title": "My Cabinet",
        "cabinet_desc": "Your personal space for focus and results.",
        "cabinet_tasks_active": "tasks in progress",
        "cabinet_my_tasks": "My Tasks",
        "cabinet_to_verify": "Pending verification",
        "projects_title": "Projects",
        "projects_create_btn": "Create Project",
        "projects_new_title": "New Project",
        "projects_placeholder_name": "Project Name",
        "projects_placeholder_desc": "Project Description",
        "projects_parent_label": "Parent Project (Folder):",
        "projects_root_option": "-- No folder (Root) --",
        "projects_empty": "No projects yet. Create the first one!",
        "projects_nested_actions": "Nested actions",
    }
}

DEFAULT_LANG = "uk"

def get_locale():
    # Priority: Cookie -> Session -> Header -> Default
    lang = request.cookies.get("lang")
    if not lang and "lang" in session:
        lang = session["lang"]
    
    if lang in TRANSLATIONS:
        return lang
        
    # Simple fallback: if 'en' is preferred in browser, use 'en', else 'uk'
    accept_lang = request.headers.get("Accept-Language", "")
    if "en" in accept_lang.lower() and not "uk" in accept_lang.lower():
         return "en"
    return DEFAULT_LANG

import urllib.parse

@app.context_processor
def inject_conf():
    lang = get_locale()
    
    def t(key):
        return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS.get(DEFAULT_LANG, {}).get(key, key))
        
    return dict(current_node=get_current_node(), t=t, current_lang=lang, quote=urllib.parse.quote)

@app.route("/lang/<lang_code>")
def switch_language(lang_code):
    resp = redirect(request.referrer or "/")
    if lang_code in TRANSLATIONS:
        session["lang"] = lang_code
        # Also set cookie for persistence and to help get_locale
        resp.set_cookie("lang", lang_code, max_age=30*24*60*60)
    return resp

def _get_type_color(name):
    # Primitive heuristic for coloring using Coral Reef theme variables
    name = name.lower()
    if "help" in name or "допом" in name: return "primary"
    if "idea" in name or "ідея" in name: return "accent-aqua"
    if "onboard" in name or "вхід" in name: return "accent-purple"
    return "muted"

@app.route("/who", methods=["GET", "POST"])
def who():
    node = get_current_node()
    if not node:
        return redirect("/")
        
    if request.method == "POST":
        name = request.form.get("name")
        if name:
            node.name = name
            db.session.commit()
        return redirect("/")
    
    return render_template("who.html", node=node)

@app.route("/read")
def read_index():
    # Show pages matching current language using primitive dictionary
    lang = get_locale()
    articles_data = KNOWLEDGE_BASE.get(lang, KNOWLEDGE_BASE[DEFAULT_LANG])
    
    # Format for template to maintain compatibility
    pages = []
    for slug, data in articles_data.items():
        pages.append({
            "slug": slug,
            "title": data["title"],
            "updated_at": datetime.utcnow() # Static for now
        })
        
    return render_template("read_index.html", pages=pages)

@app.route("/read/<slug>")
def read_page(slug):
    lang = get_locale()
    
    # Try current language
    articles_data = KNOWLEDGE_BASE.get(lang, KNOWLEDGE_BASE.get(DEFAULT_LANG, {}))
    article = articles_data.get(slug)
    
    # Fallback to other language if missing
    if not article:
        other_lang = "en" if lang == "uk" else "uk"
        article = KNOWLEDGE_BASE.get(other_lang, {}).get(slug)
        
    if not article:
        return render_template("404.html"), 404
        
    # Try to use 'markdown' library for rich text
    try:
        import markdown
        content_html = markdown.markdown(article["content"], extensions=['tables', 'fenced_code'])
    except:
        content_html = article["content"].replace("\n", "<br>")
        
    page = {
        "title": article["title"],
        "content": article["content"],
        "updated_at": datetime.utcnow()
    }
    
    return render_template("read_page.html", page=page, content_html=content_html)

@app.route("/qr")
def qr_gen():
    text = request.args.get("text", "")
    if not text:
        return "No text provided", 400
        
    img = qrcode.make(text)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route("/types")
def action_types():
    node = get_current_node()
    types = ActionType.query.order_by(ActionType.name).all()
    return render_template("action_types.html", types=types, node=node)

@app.route("/types/new", methods=["POST"])
def create_action_type():
    node = get_current_node()
    if not node: return redirect("/")
    
    name = request.form.get("name")
    description = request.form.get("description")
    schema_json = request.form.get("schema") # User provides JSON body for now or simple fields
    
    # Fallback if manual JSON is hard: simple key-value generator could be added later
    # For MVP we assume valid JSON or simple text
    try:
        json.loads(schema_json) # Validate
    except:
        schema_json = json.dumps({"fields": [{"name":"note", "type":"text"}]})

    new_type = ActionType(
        name=name,
        description=description,
        schema=schema_json,
        creator_id=node.id
    )
    db.session.add(new_type)
    db.session.commit()
    return redirect("/types")

@app.route("/do/<type_id>", methods=["GET", "POST"])
def do_action(type_id):
    node = get_current_node()
    if not node: return redirect("/")
    
    act_type = ActionType.query.get_or_404(type_id)
    schema = json.loads(act_type.schema)
    projects = Project.query.filter_by(status='active').all()
    
    if request.method == "POST":
        payload_data = {}
        for field in schema.get("fields", []):
            fname = field.get("name")
            payload_data[fname] = request.form.get(fname)
            
        req_witnesses = int(request.form.get("required_witnesses", 1))
        project_id = request.form.get("project_id")
        if project_id == "none": project_id = None
        
        evidence_photo = request.form.get("evidence_photo") # Base64
        keep_evidence = request.form.get("keep_evidence") == "on"
        
        new_action = Action(
            action_type_id=act_type.id,
            node_id=node.id,
            payload=json.dumps(payload_data),
            status='proposed',
            required_witnesses=req_witnesses,
            project_id=project_id,
            evidence_photo=evidence_photo,
            keep_evidence=keep_evidence
        )
        db.session.add(new_action)
        db.session.commit()
        return redirect("/")
        
    return render_template("do_action.html", type=act_type, schema=schema, projects=projects)

@app.route("/action/<action_id>/take")
def take_action(action_id):
    node = get_current_node()
    if not node: return redirect("/")
    
    action = Action.query.get_or_404(action_id)
    if action.status == 'proposed' and not action.assignee_node_id:
        action.assignee_node_id = node.id
        action.status = 'in_progress'
        db.session.commit()
    return redirect("/")

@app.route("/action/<action_id>/complete")
def complete_action(action_id):
    node = get_current_node()
    if not node: return redirect("/")
    
    action = Action.query.get_or_404(action_id)
    if action.assignee_node_id == node.id and action.status == 'in_progress':
        action.status = 'completed'
        db.session.commit()
    return redirect("/")

@app.route("/action/<action_id>/verify")
def verify_action(action_id):
    node = get_current_node()
    if not node: return redirect("/")
    
    action = Action.query.get_or_404(action_id)
    if action.status != 'completed':
        return redirect("/")
        
    # Check if node is allowed to witness
    if action.allowed_witnesses:
        allowed = json.loads(action.allowed_witnesses)
        if node.id not in allowed:
            return "You are not an allowed witness for this action.", 403

    witnesses = json.loads(action.witnesses_data) if action.witnesses_data else []
    if node.id in [w['node_id'] for w in witnesses]:
        return redirect("/") # Already witnessed
        
    witnesses.append({
        "node_id": node.id,
        "name": node.name,
        "time": datetime.utcnow().isoformat()
    })
    action.witnesses_data = json.dumps(witnesses)
    
    if len(witnesses) >= action.required_witnesses:
        action.status = 'verified'
        # Automatic Cleanup of evidence if requested
        if not action.keep_evidence:
            action.evidence_photo = None
            
    db.session.commit()
    return redirect("/")

@app.route("/projects")
def project_list():
    node = get_current_node()
    projects = Project.query.filter_by(parent_id=None).all()
    return render_template("projects.html", projects=projects, node=node)

@app.route("/projects/new", methods=["POST"])
def create_project():
    node = get_current_node()
    if not node: return redirect("/")
    
    name = request.form.get("name")
    desc = request.form.get("description")
    parent_id = request.form.get("parent_id")
    if parent_id == "none": parent_id = None
    
    new_project = Project(
        name=name,
        description=desc,
        creator_node_id=node.id,
        parent_id=parent_id
    )
    db.session.add(new_project)
    db.session.commit()
    return redirect("/projects")

@app.route("/cabinet")
def cabinet():
    node = get_current_node()
    if not node: return redirect("/who")
    
    # Actions I'm working on
    my_tasks = Action.query.filter_by(assignee_node_id=node.id).filter(Action.status != 'verified').all()
    
    # Actions I created that need verification
    to_verify = Action.query.filter_by(node_id=node.id, status='completed').all()
    
    # Projects I'm participating in
    participations = Participation.query.filter_by(node_id=node.id).all()
    my_projects = [p.project for p in participations]
    
    return render_template("cabinet.html", tasks=my_tasks, to_verify=to_verify, projects=my_projects, node=node)

@app.route("/project/<project_id>")
def project_view(project_id):
    project = Project.query.get_or_404(project_id)
    backlog = [a for a in project.actions if a.status == 'proposed']
    active = [a for a in project.actions if a.status in ['in_progress', 'completed']]
    archive = [a for a in project.actions if a.status == 'verified']
    
    node = get_current_node()
    is_member = any(p.node_id == node.id for p in project.participants) if node else False
    
    return render_template("project_view.html", project=project, backlog=backlog, active=active, archive=archive, is_member=is_member)

@app.route("/project/<project_id>/join")
def join_project(project_id):
    node = get_current_node()
    if not node: return redirect("/who")
    
    # Check if already joined
    exists = Participation.query.filter_by(project_id=project_id, node_id=node.id).first()
    if not exists:
        part = Participation(project_id=project_id, node_id=node.id, role='member')
        db.session.add(part)
        db.session.commit()
    return redirect(f"/project/{project_id}")

@app.route("/project/<project_id>/milestone/new", methods=["POST"])
def create_milestone(project_id):
    node = get_current_node()
    project = Project.query.get_or_404(project_id)
    
    name = request.form.get("name")
    desc = request.form.get("description")
    deadline_str = request.form.get("deadline")
    deadline = datetime.fromisoformat(deadline_str) if deadline_str else None
    
    new_m = Milestone(project_id=project_id, name=name, description=desc, deadline=deadline)
    db.session.add(new_m)
    db.session.commit()
    return redirect(f"/project/{project_id}")

@app.route("/stats")
def stats():
    # Simple count by type
    stats_data = db.session.query(
        ActionType.name, db.func.count(Action.id)
    ).join(Action).group_by(ActionType.name).all()
    
    return render_template("stats.html", stats=stats_data)

# --- SYNC (P2P Primitive) ---

@app.route("/sync", methods=["GET", "POST"])
def sync_page():
    node = get_current_node()
    my_ip = get_local_ip()
    port = request.environ.get('SERVER_PORT', '5000')
    my_address = f"http://{my_ip}:{port}"
    
    msg = ""
    
    if request.method == "POST":
        peer_address = request.form.get("peer_address")
        if peer_address:
            try:
                # 1. Pull data
                if not peer_address.startswith("http"):
                    peer_address = "http://" + peer_address
                
                resp = requests.get(f"{peer_address}/api/sync/export", timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    imported_count = merge_db(data)
                    
                    # Update Peer Logic
                    peer_obj = Peer.query.filter_by(ip_address=peer_address).first()
                    if not peer_obj:
                        peer_obj = Peer(ip_address=peer_address)
                        db.session.add(peer_obj)
                    peer_obj.last_success = datetime.utcnow()
                    peer_obj.failure_count = 0
                    db.session.commit()
                    
                    msg = f"Successfully synced! Imported {imported_count} new items."
                else:
                    msg = f"Error: Peer returned {resp.status_code}"
            except Exception as e:
                msg = f"Sync failed: {str(e)}"
    
    return render_template("sync.html", my_address=my_address, msg=msg)

@app.route("/replicate")
def replicate_page():
    my_ip = get_local_ip()
    port = request.environ.get('SERVER_PORT', '5000')
    my_address = f"http://{my_ip}:{port}"
    
    # Detect if request is from the same machine (localhost or own LAN IP)
    remote_addr = request.remote_addr
    is_local = remote_addr in ['127.0.0.1', '::1', my_ip]
    
    return render_template("replication.html", my_address=my_address, is_local=is_local)

@app.route("/install.sh")
def install_script():
    my_ip = get_local_ip()
    port = request.environ.get('SERVER_PORT', '5000')
    host = f"http://{my_ip}:{port}"
    
    script = f"""#!/bin/bash
echo ">>> EME NODE INSTALLER <<<"
echo "Target: {host}"

# 1. Update and upgrade
pkg update -y && pkg upgrade -y

# 2. Install Python and Git
pkg install python git -y

# 3. Install system dependencies for Pillow (CRITICAL for Termux)
pkg install libjpeg-turbo zlib libpng freetype clang make libwebp -y

# 4 Upgrade pip
pip install --upgrade pip wheel

# 2. Setup directory
mkdir -p eme
cd eme

# 3. Download Bundle (Source + DB)
echo "Downloading EME Bundle..."
curl -o bundle.zip {host}/bundle.zip

# 4. Unzip
echo "Unzipping..."
unzip -o bundle.zip
rm bundle.zip

# 8. Install Python dependencies with proper flags for Pillow
echo "Installing Python dependencies..."
LDFLAGS="-L$PREFIX/lib" CFLAGS="-I$PREFIX/include" pip install flask flask-sqlalchemy requests qrcode[pil] markdown || echo "Warning: Some packages may need internet"

# 9. Verify
echo "Verifying dependencies..."
python -c "from PIL import Image; import flask, qrcode, markdown; print('All dependencies OK!')" || {{ echo "ERROR: Connect to internet and run: LDFLAGS=\"-L\$PREFIX/lib\" CFLAGS=\"-I\$PREFIX/include\" pip install -r requirements.txt"; exit 1; }}

echo "Installation Complete."
echo "Running EME Node..."
python app.py
"""
    return Response(script, mimetype='text/plain')

@app.route("/bundle.zip")
def download_bundle():
    # Use absolute paths based on the location of this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a zip of app.py, templates, and eme.db in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add app.py
        app_path = os.path.join(base_dir, "app.py")
        if os.path.exists(app_path):
            zf.write(app_path, arcname="app.py")
        
        # Add templates
        templates_dir = os.path.join(base_dir, "templates")
        if os.path.exists(templates_dir):
            for root, dirs, files in os.walk(templates_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, base_dir)
                    zf.write(full_path, arcname=rel_path)
        
        # Add static (if exists)
        static_dir = os.path.join(base_dir, "static")
        if os.path.exists(static_dir):
             for root, dirs, files in os.walk(static_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, base_dir)
                    zf.write(full_path, arcname=rel_path)

        # IMPORTANT: We DO NOT include eme.db here to ensure a clean start for new nodes.
        # If needed, a separate sync/replication process handles data transfer.
        # db_path = os.path.join(base_dir, "eme.db")
        # if os.path.exists(db_path):
        #     zf.write(db_path, arcname="eme.db")
            
        # Add Knowledge Base
        kb_path = os.path.join(base_dir, "knowledge_base.py")
        if os.path.exists(kb_path):
            zf.write(kb_path, arcname="knowledge_base.py")
            
    memory_file.seek(0)
    return send_file(memory_file, download_name="eme_bundle.zip", as_attachment=True)

@app.route("/api/sync/export")
def sync_export_api():
    # Dump everything for a full mesh sync
    nodes = Node.query.all()
    types = ActionType.query.all()
    projects = Project.query.all()
    milestones = Milestone.query.all()
    participations = Participation.query.all()
    actions = Action.query.all()
    
    data = {
        "nodes": [{
            "id": n.id, "device_id": n.device_id, "name": n.name, 
            "created_at": n.created_at.isoformat(), "last_seen": n.last_seen.isoformat()
        } for n in nodes],
        "types": [{
            "id": t.id, "name": t.name, "description": t.description, "schema": t.schema, 
            "creator_id": t.creator_id, "created_at": t.created_at.isoformat()
        } for t in types],
        "projects": [{
            "id": p.id, "name": p.name, "description": p.description, 
            "category_id": p.category_id, "creator_node_id": p.creator_node_id,
            "parent_id": p.parent_id, "status": p.status, 
            "definition_of_done": p.definition_of_done, "created_at": p.created_at.isoformat()
        } for p in projects],
        "milestones": [{
            "id": m.id, "project_id": m.project_id, "name": m.name, 
            "description": m.description, "deadline": m.deadline.isoformat() if m.deadline else None,
            "status": m.status, "created_at": m.created_at.isoformat()
        } for m in milestones],
        "participations": [{
            "id": pr.id, "project_id": pr.project_id, "node_id": pr.node_id, 
            "role": pr.role, "created_at": pr.created_at.isoformat()
        } for pr in participations],
        "actions": [{
            "id": a.id, "type_id": a.action_type_id, "node_id": a.node_id, 
            "assignee_node_id": a.assignee_node_id, "project_id": a.project_id,
            "milestone_id": a.milestone_id, "payload": a.payload, "status": a.status,
            "required_witnesses": a.required_witnesses, "allowed_witnesses": a.allowed_witnesses,
            "witnesses_data": a.witnesses_data, "evidence_photo": a.evidence_photo,
            "keep_evidence": a.keep_evidence, "created_at": a.created_at.isoformat()
        } for a in actions]
    }
    return jsonify(data)

def merge_db(data):
    count = 0
    node_map = {} # remote_id -> local_id
    
    # 1. Merge Nodes (Handle Device ID collisions)
    for n_data in data.get("nodes", []):
        remote_id = n_data["id"]
        dev_id = n_data["device_id"]
        
        # Check by ID first
        local_node = Node.query.get(remote_id)
        if local_node:
            node_map[remote_id] = local_node.id
            if n_data.get("name"): # Update name if newer? Let's just keep local for now or update if empty
                 if not local_node.name:
                     local_node.name = n_data["name"]
            continue
            
        # Check by Device ID (The Fix for 'System' node and others)
        local_node_by_dev = Node.query.filter_by(device_id=dev_id).first()
        if local_node_by_dev:
            # Conflict found: Remote has same DeviceID but different UUID.
            # Map remote UUID to local UUID.
            node_map[remote_id] = local_node_by_dev.id
            continue
            
        # New Node
        new_node = Node(
            id=remote_id,
            device_id=dev_id,
            name=n_data["name"],
            created_at=datetime.fromisoformat(n_data["created_at"]),
            last_seen=datetime.fromisoformat(n_data["last_seen"])
        )
        db.session.add(new_node)
        node_map[remote_id] = remote_id # Map to itself
    
    db.session.flush() # Ensure new nodes have IDs usable for FKs if needed (though we set them manually)

    # 2. Merge Types
    # Types don't have a unique constraint on Name, so strictly speaking duplicates are possible.
    # But ideally we should dedup by Name if created by System? 
    # For now, we'll just check ID to avoid crash. 
    # Improvement: Map types by name if they are "System" types? 
    # Let's keep it simple for MVP: Trust UUIDs for types.
    for t_data in data.get("types", []):
        if not ActionType.query.get(t_data["id"]):
            # Remap creator_id if needed
            creator_id = t_data["creator_id"]
            if creator_id in node_map:
                creator_id = node_map[creator_id]
                
            new_type = ActionType(
                id=t_data["id"],
                name=t_data["name"],
                description=t_data["description"],
                schema=t_data["schema"],
                creator_id=creator_id,
                created_at=datetime.fromisoformat(t_data["created_at"])
            )
            db.session.add(new_type)
            count += 1
            
    db.session.flush()

    # 3. Merge Projects
    for p_data in data.get("projects", []):
        if not Project.query.get(p_data["id"]):
            creator_id = p_data["creator_node_id"]
            if creator_id in node_map: creator_id = node_map[creator_id]
            
            new_project = Project(
                id=p_data["id"],
                name=p_data["name"],
                description=p_data["description"],
                category_id=p_data["category_id"],
                creator_node_id=creator_id,
                parent_id=p_data["parent_id"],
                status=p_data["status"],
                definition_of_done=p_data["definition_of_done"],
                created_at=datetime.fromisoformat(p_data["created_at"])
            )
            db.session.add(new_project)
            count += 1
    db.session.flush()

    # 4. Merge Milestones
    for m_data in data.get("milestones", []):
        if not Milestone.query.get(m_data["id"]):
            new_m = Milestone(
                id=m_data["id"],
                project_id=m_data["project_id"],
                name=m_data["name"],
                description=m_data["description"],
                deadline=datetime.fromisoformat(m_data["deadline"]) if m_data["deadline"] else None,
                status=m_data["status"],
                created_at=datetime.fromisoformat(m_data["created_at"])
            )
            db.session.add(new_m)
            count += 1
    db.session.flush()

    # 5. Merge Participations
    for pr_data in data.get("participations", []):
        if not Participation.query.get(pr_data["id"]):
            n_id = pr_data["node_id"]
            if n_id in node_map: n_id = node_map[n_id]
            
            new_pr = Participation(
                id=pr_data["id"],
                project_id=pr_data["project_id"],
                node_id=n_id,
                role=pr_data["role"],
                created_at=datetime.fromisoformat(pr_data["created_at"])
            )
            db.session.add(new_pr)
            count += 1
    db.session.flush()

    # 6. Merge Actions
    for a_data in data.get("actions", []):
        if Action.query.get(a_data["id"]):
            continue
            
        r_node_id = a_data["node_id"]
        local_node_id = node_map.get(r_node_id, r_node_id)
        
        assignee_id = a_data.get("assignee_node_id")
        if assignee_id in node_map: assignee_id = node_map[assignee_id]

        new_action = Action(
            id=a_data["id"],
            action_type_id=a_data["type_id"],
            node_id=local_node_id,
            assignee_node_id=assignee_id,
            project_id=a_data.get("project_id"),
            milestone_id=a_data.get("milestone_id"),
            payload=a_data["payload"],
            status=a_data.get("status", "proposed"),
            required_witnesses=a_data.get("required_witnesses", 1),
            allowed_witnesses=a_data.get("allowed_witnesses"),
            witnesses_data=a_data.get("witnesses_data"),
            evidence_photo=a_data.get("evidence_photo"),
            keep_evidence=a_data.get("keep_evidence", False),
            created_at=datetime.fromisoformat(a_data["created_at"])
        )
        db.session.add(new_action)
        count += 1
    
    db.session.commit()
    return count

# --- INIT ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        migrate_db_schema() # Ensure existing tables have all columns
        
        # Seed default help type if empty
        if not ActionType.query.first():
            # Create a "System" node for seeding with FIXED UUID to avoid sync conflicts
            SYSTEM_UUID = "00000000-0000-0000-0000-000000000000"
            sys_node = Node(id=SYSTEM_UUID, device_id="system", name="System")
            db.session.add(sys_node)
            
            help_type = ActionType(
                name="Допомога",
                description="Пряма допомога людині",
                schema=json.dumps({
                    "fields": [
                        {"name": "recipient", "label": "Кому", "type": "text"},
                        {"name": "summary", "label": "Що зробив", "type": "text"}
                    ]
                }),
                creator_id=sys_node.id
            )
            db.session.add(help_type)
            db.session.commit()
            
        # No more page seeding needed
        db.session.commit()

            
    # Start Auto-Sync Thread
    def run_auto_sync():
        while True:
            time.sleep(3600) # Every hour
            with app.app_context():
                peers = Peer.query.all()
                for p in peers:
                    try:
                        resp = requests.get(f"{p.ip_address}/api/sync/export", timeout=10)
                        if resp.status_code == 200:
                            merge_db(resp.json())
                            p.last_success = datetime.utcnow()
                            p.failure_count = 0
                        else:
                            p.failure_count += 1
                    except:
                        p.failure_count += 1
                db.session.commit()

    t = threading.Thread(target=run_auto_sync, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=5000, debug=True)
