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

class Action(db.Model):
    __tablename__ = 'actions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action_type_id = db.Column(db.String(36), db.ForeignKey('action_types.id'), nullable=False)
    node_id = db.Column(db.String(36), db.ForeignKey('nodes.id'), nullable=False)
    payload = db.Column(db.Text, nullable=False) # JSON with actual data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    node = db.relationship('Node', backref='actions')
    action_type = db.relationship('ActionType', backref='actions')

class Peer(db.Model):
    __tablename__ = 'peers'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address = db.Column(db.String(100), unique=True, nullable=False)
    last_success = db.Column(db.DateTime, nullable=True)
    failure_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- HELPERS ---

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
    try:
        # Hack to find local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
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
        # We assign a device_id and create a Node immediately (Implicit Onboarding)
        new_device_id = str(uuid.uuid4())
        new_node = Node(device_id=new_device_id, name="New Node")
        db.session.add(new_node)
        db.session.commit()
        
        session["node_id"] = new_node.id
        resp = make_response(redirect("/who")) # Redirect to set name
        resp.set_cookie("device_id", new_device_id, max_age=60*60*24*365*10) # 10 years
        return resp

    # Fetch recent actions
    actions = Action.query.order_by(Action.created_at.desc()).limit(50).all()
    
    # Parse payloads for display
    display_actions = []
    for a in actions:
        try:
            data = json.loads(a.payload)
        except:
            data = {}
        display_actions.append({
            "who": a.node.name or "Anonymous",
            "type": a.action_type.name,
            "data": data,
            "when": a.created_at.strftime("%Y-%m-%d %H:%M"),
            "color": _get_type_color(a.action_type.name)
        })

    return render_template("index.html", actions=display_actions, current_node=node)

# --- INTERNATIONALIZATION (Offline) ---
TRANSLATIONS = {
    "uk": {
        "nav_home": "Головна",
        "nav_knowledge": "Знання",
        "nav_types": "Типи",
        "nav_stats": "Статистика",
        "nav_sync": "SYNC",
        "nav_repl": "Node+",
        "nav_who": "👤",
        "footer_text": "EME Index v0.1 • Вузол",
        "guest": "Гість",
        "lang_switch": "EN",
        "actions_title": "Індекс Дій",
        "btn_add_action": "+ Додати дію",
        "btn_filter": "Фільтр",
        "placeholder_search": "Пошук...",
        "no_actions": "Поки що немає записів.",
        "read_back": "← До списку",
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
        "scan_btn": "📷 Сканувати QR",
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
    },
    "en": {
        "nav_home": "Home",
        "nav_knowledge": "Knowledge",
        "nav_types": "Types",
        "nav_stats": "Stats",
        "nav_sync": "SYNC",
        "nav_repl": "Node+",
        "nav_who": "👤",
        "footer_text": "EME Index v0.1 • Node",
        "guest": "Guest",
        "lang_switch": "UA",
        "actions_title": "Action Index",
        "btn_add_action": "+ Add Action",
        "btn_filter": "Filter",
        "placeholder_search": "Search...",
        "no_actions": "No records yet.",
        "read_back": "← Back to list",
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
        "scan_btn": "📷 Scan QR",
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
    # Primitive heuristic for coloring
    name = name.lower()
    if "help" in name or "допом" in name: return "green"
    if "idea" in name or "ідея" in name: return "yellow"
    if "onboard" in name or "вхід" in name: return "blue"
    return "gray"

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
    
    if request.method == "POST":
        # Extract fields based on schema
        payload_data = {}
        for field in schema.get("fields", []):
            fname = field.get("name")
            fval = request.form.get(fname)
            payload_data[fname] = fval
            
        new_action = Action(
            action_type_id=act_type.id,
            node_id=node.id,
            payload=json.dumps(payload_data)
        )
        db.session.add(new_action)
        db.session.commit()
        return redirect("/")
        
    return render_template("do_action.html", type=act_type, schema=schema)

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
    return render_template("replication.html", my_address=my_address)

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
    # Create a zip of app.py, templates, and eme.db in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add app.py
        zf.write("app.py")
        
        # Add templates
        for root, dirs, files in os.walk("templates"):
            for file in files:
                zf.write(os.path.join(root, file))
        
        # Add static (if exists)
        if os.path.exists("static"):
             for root, dirs, files in os.walk("static"):
                for file in files:
                    zf.write(os.path.join(root, file))

        # Add DB
        if os.path.exists("eme.db"):
            zf.write("eme.db")
            
    memory_file.seek(0)
    return send_file(memory_file, download_name="eme_bundle.zip", as_attachment=True)

@app.route("/api/sync/export")
def sync_export_api():
    # Dump everything
    nodes = Node.query.all()
    types = ActionType.query.all()
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
        "actions": [{
            "id": a.id, "type_id": a.action_type_id, "node_id": a.node_id, 
            "payload": a.payload, "created_at": a.created_at.isoformat()
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

    # 3. Merge Actions
    for a_data in data.get("actions", []):
        if Action.query.get(a_data["id"]):
            continue
            
        # Remap node_id
        r_node_id = a_data["node_id"]
        local_node_id = node_map.get(r_node_id, r_node_id)
        
        # Ensure Foreign Keys exist
        # If Type is missing (rare case if sync order is correct), we skip
        if not ActionType.query.get(a_data["type_id"]):
             continue
             
        # If Node is missing (shouldn't happen with map), skip
        if not Node.query.get(local_node_id):
             continue

        new_action = Action(
            id=a_data["id"],
            action_type_id=a_data["type_id"],
            node_id=local_node_id,
            payload=a_data["payload"],
            created_at=datetime.fromisoformat(a_data["created_at"])
        )
        db.session.add(new_action)
        count += 1
    
    db.session.flush()

    db.session.commit()
    return count

# --- INIT ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
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
