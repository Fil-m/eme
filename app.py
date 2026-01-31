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

class Page(db.Model):
    __tablename__ = 'pages'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    }
}

DEFAULT_LANG = "uk"

def get_locale():
    # Check session first, then simple browser negotiation
    if "lang" in session:
        return session["lang"]
    # Simple fallback: if 'en' is preferred in browser, use 'en', else 'uk'
    # This avoids complex Babel dependencies for now
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
    if lang_code in TRANSLATIONS:
        session["lang"] = lang_code
    return redirect(request.referrer or "/")

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
    # Filter out English pages from the main list (they are auxiliary)
    pages = Page.query.filter(Page.slug.notlike('%-en')).all()
    return render_template("read_index.html", pages=pages)

@app.route("/read/<slug>")
def read_page(slug):
    # ... (existing content) ...
    # Bilingual Logic:
    # If user is in English mode, try to find the -en version of this page.
    target_slug = slug
    lang = get_locale()
    
    if lang == 'en':
        en_slug = slug + "-en"
        en_page = Page.query.filter_by(slug=en_slug).first()
        if en_page:
            target_slug = en_slug
            
    page = Page.query.filter_by(slug=target_slug).first_or_404()
    
    # Try to use 'markdown' library for rich text (tables, bold, etc.)
    try:
        import markdown
        # Enable tables and other useful extensions
        content_html = markdown.markdown(page.content, extensions=['tables', 'fenced_code'])
    except ImportError:
        # Fallback to simple line-based formatting if lib not installed
        content_html = ""
        lines = page.content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                content_html += "<br>"
                continue
                
            # Basic styling
            if line.startswith('###'):
                content_html += f"<h3>{line[3:].strip()}</h3>"
            elif line.startswith('##'):
                content_html += f"<h2>{line[2:].strip()}</h2>"
            elif line.startswith('#'):
                content_html += f"<h1>{line[1:].strip()}</h1>"
            elif line.startswith('|'): 
                content_html += f"<pre>{line}</pre>"
            elif line.startswith('- ') or line.startswith('* '):
                 content_html += f"<li>{line[2:]}</li>"
            else:
                line = line.replace('**', '<b>').replace('**', '</b>')
                content_html += f"<p>{line}</p>"

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
    pages = Page.query.all()
    
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
        } for a in actions],
        "pages": [{
            "id": p.id, "slug": p.slug, "title": p.title, "content": p.content,
            "updated_at": p.updated_at.isoformat()
        } for p in pages]
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

    # 4. Merge Pages
    for p_data in data.get("pages", []):
        existing = Page.query.filter_by(slug=p_data["slug"]).first()
        remote_update = datetime.fromisoformat(p_data["updated_at"])
        
        if not existing:
            new_page = Page(
                id=p_data["id"],
                slug=p_data["slug"],
                title=p_data["title"],
                content=p_data["content"],
                updated_at=remote_update
            )
            db.session.add(new_page)
            count += 1
        else:
            # Simple conflict resolution: newest wins
            if remote_update > existing.updated_at:
                existing.title = p_data["title"]
                existing.content = p_data["content"]
                existing.updated_at = remote_update
                count += 1

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
            
        # Seed Pages
        seed_content = {
            "manifest": ("Маніфест EME", """EME — Люди для людей
EME — це люди, які будують світ, де допомога — норма, а взаємодія — щоденна практика.
Ми віримо: кожен може бути вузлом підтримки, і кожна дія має значення.
Ми доводимо, що нова реальність можлива вже сьогодні — локально, конкретно, нами самими.

1. Призначення
Ми створюємо мережу взаємодопомоги, де люди не ізольовані, а з’єднані дією.
Технології служать людям, а не навпаки.
Мала дія, якщо вона відтворювана і поділена, змінює світ.

2. Принципи
Дія важить більше за слова — роби, і світ побачить результат.
Горизонтальність — немає центру, немає керівників. Всі рівні у здатності допомагати.
Прозорість — ресурси, знання, досвід відкриті для всіх.
Реальність понад утопію — ми створюємо функціональне тут і зараз.
Суб’єктність кожного — ти важливий і можеш приймати рішення.
Відтворюваність — наші практики легко повторювати в будь-якому місті, в будь-якому контексті.
Самодостатність: кожен вузол прагне максимальної автономії в базових потребах (їжа, енергія, знання, здоров’я, робота). Ми обмінюємося навичками та ресурсами, щоб кожен міг стати незалежнішим, а не залежнішим від системи.

3. Дія та взаємодія
Ми об’єднуємо людей через спільні проєкти, навчання та події.
Використовуємо технології, простір і знання як інструменти підтримки.
Розширюємо мережу через спільні цінності та практику, без ієрархії.
Фіксуємо досвід і передаємо його далі, щоб з’являлися нові вузли.

4. Візія
Ми прагнемо суспільства, де:
допомога природна, а не подвиг;
довіра практикується щодня;
технології і люди співпрацюють;
мережа підтримки розростається, а ізоляція зникає;
кожна дія стає цеглинкою нової реальності.

5. Заклик
EME існує, щоб ти долучився.
Щоб ти став вузлом, а не глядачем.
Щоб ми разом творили новий світ — тут і зараз, нами самими, щодня.
EME — люди для людей.
Це емерджентність: коли ми разом, виникає щось більше, ніж ми окремо.
І це лише початок. Це для цього руху. Для індексації дій."""),

            "responsibility": ("Відповідальність", """1. Природа відповідальності
В EME відповідальність не каральна, а стабілізуюча.
Вона служить захисту мережі та її вузлів, а не обтяженню окремих учасників.
Відповідальність — це імунітет системи, який локалізує наслідки та дозволяє мережі рости.

2. Локальна відповідальність
Кожен вузол відповідає тільки за свій конкретний внесок, без необхідності «тягнути всю систему».
Це дозволяє:
- зберігати енергію та ресурси учасників
- уникати перевантаження і вигорання
- підвищувати стійкість мережі

3. Відтворюваність і реплікація
Всі практики EME можна легко повторювати.
Кожен учасник, отримавши підтримку або долучившись до проєкту, стає вузлом, який:
- відтворює практики
- передає знання і досвід
- розширює мережу, не концентруючи навантаження на окремому вузлі

4. Зворотний зв’язок
Наслідки дій вузла фіксуються прозоро, щоб:
- учасники бачили ефект своєї дії
- система адаптувала практики під нові обставини
- навчання відбувалося без покарань

5. Підтримка вузлів
Мережа оберігає свої вузли:
- надає ресурси для відновлення
- ділиться знанням для ефективної роботи
- стимулює взаємопідтримку
Кожен вузол залишається активним і здатним діяти довго, що збільшує стійкість системи.

6. Коротка формула
Відповідальність EME = локалізація наслідків + захист вузлів + відтворюваність практик
→ система зростає, вузли залишаються сильними, мережа самореплікується"""),

            "protocol": ("Протокол взаємодії", """Протокол взаємодії EME (версія 1.0 — для самореплікації мережі)
Цей документ описує прості, повторювані кроки, які кожен вузол може виконувати самостійно.
Мета — мережа росте горизонтально, без центру, через чіткі алгоритми дій.
Кожен новий вузол стає здатним створювати нові вузли.

1. Вхід нового вузла в мережу
(онбординг — 3–5 хвилин + 1 день)

Крок 1. Знайомство
Людина знаходить EME (через друга, пост, #EME1на1, канал/чат).
Читає короткий маніфест + Кодекс вузла (1 сторінка).
Задає питання в загальному чаті або безпосередньо вузлу, який запросив.

Крок 2. Самоініціація (сам себе вводить)
Пише в чат/канал повідомлення:
«Привіт, я [ім'я або псевдо]. Хочу бути вузлом EME. Готовий робити мінімум 1 дію підтримки щодня. Мій перший внесок: [коротко про себе або чому долучаюсь].»
Отримує привітання + посилання на основні чати/канали/шаблони.
(Опціонально) Додає себе в список вузлів, якщо є спільний документ або бот.

Крок 3. Перший тиждень — адаптація
Виконує правило 1/1 щодня.
Читає/переглядає 3–5 постів з досвідом (уроки, історії).
Запитує в чаті: «Чим можу допомогти зараз?» або «Що потрібно спільноті?».
Запрошує хоча б 1 людину (друга, знайомого) — просто кидає посилання на маніфест.
Результат: новий вузол активний за 1–3 дні, без «затвердження» від когось.

2. Передача знання та досвіду
(щоб мережа не втрачала пам’ять при рості)
Кожна дія/проєкт/допомога фіксується коротко:
Що зробив → Для кого → Результат → Що спрацювало / не спрацювало (1–3 речення).
Приклад: «Допоміг з резюме — людина отримала запрошення на співбесіду. Спрацювало: конкретні приклади з вакансії. Не спрацювало: надто довгий текст.»
Де фіксувати (вибір вузла):
- Загальний канал/чат з тегом #EMEдосвід або #EMEурок
- Окремий документ/ноушн/гітхаб (якщо є тех-вузли)
- Сторіз/пост з #EME1на1 (для видимості)

Щотижня один вузол (будь-хто) робить «тижневий дайджест»:
3–5 найкорисніших уроків/шаблонів за тиждень → постить у загальний канал.
Це створює «колективну пам’ять» без центру.

Шаблони передачі:
«Як я організував…» (зустріч, збір ресурсів, онлайн-допомога)
«Готовий шаблон: [назва]» (копіюй-встав для повторення)
«Помилка тижня: [опис] → як уникнути»

3. Фіксація помилок та уроків
(щоб мережа вчилася, а не повторювала)
Правило «без провини»: помилка — це ресурс для всіх.
Коли щось пішло не так (вигорання, конфлікт, невдала допомога):
Пишеш коротко: «Урок: [що сталося] → чому → що робити інакше».
Додаєш тег #EMEурок або #EMEпомилка.
Якщо конфлікт — використовуєш правило з Кодексу: говори безпосередньо, спокійно, без публіки.

Щомісяця (або коли накопичиться 10+ уроків) — «колективний огляд»:
Будь-хто може ініціювати пост: «Збираємо топ-5 уроків місяця».
Обговорюємо 10–15 хвилин у голосовому чаті (якщо є).
Оновлюємо «Базу уроків» (один документ або канал-пін).
Якщо урок критичний (наприклад, про кордони, безпеку, вигорання) — робимо його «постійним піном» у чаті.

Одна фраза-пам’ятка для всіх вузлів:
«Я фіксую свій досвід → ділюся ним → мережа вчиться → нові вузли стартують швидше.»

Цей протокол — не догма.
Кожен локальний вузол/чат може адаптувати його під себе (наприклад, додати бота для фіксації, окремий канал для уроків).
Головне — повторюваність і прозорість: кожен знає, що робити, щоб мережа росла сама.
EME — емерджентна мережа.
Протокол робить її стійкою та масштабованою."""),

            "codex": ("Кодекс Вузла", """Кодекс вузла / прості правила дії

Що робить вузол щодня / щотижня:
- Робить мінімум 1 дію підтримки.
- Фіксує результат в індексі.
- Береже себе (пауза без провини).

Одна сторінка, максимум дві, легко запам’ятовується.
Приклад: «Щоденний внесок = маленька дія на користь іншого вузла / спільноти».

2. Протокол взаємодії
Формалізує процеси:
- Як новий вузол входить у мережу
- Як передається знання / досвід
- Як фіксуються помилки / уроки
Цей документ дозволяє системі самореплікуватися, бо кожен знає алгоритм дій.

3. Дошка досвіду / фіксації практик
Реєстр практик, проєктів, успішних дій вузлів
Візуальна або цифрова форма
Забезпечує відтворюваність та навчання через досвід

4. План розширення мережі
Вказує:
- Як залучати нові вузли
- Як організовувати локальні події або онлайн-активності
- Як створювати локальні копії практик
Мета: самореплікація без централізованого управління

5. Документ про підтримку вузлів
Як мережа захищає учасників:
- Ресурси для відновлення (час, знання, енергія)
- Методи контролю навантаження
- Канали взаємопідтримки
Це гарантує, що вузли не вигорають, а система залишається стійкою

6. Метрики та сигналізація
Простий документ для зворотного зв’язку системи:
- Як оцінювати ефективність дій вузлів
- Як помічати слабкі місця або перевантаження
- Як відстежувати відтворюваність практик

7. Візуальні схеми / мапи руху
Мережа, вузли, потоки дій, точки відповідальності
Мета: новий учасник одразу бачить, як працює рух
Зручно для презентацій, залучення нових вузлів"""),

            "experience_board": ("Дошка досвіду", """3. Дошка досвіду EME
(Реєстр практик, проєктів та успішних дій вузлів)

Мета: забезпечити **відтворюваність** — щоб будь-який вузол міг скопіювати успішну практику за 5–10 хвилин, навчитися на чужому досвіді та уникнути повторення помилок.
Це не вікі-статті, а живий реєстр коротких, готових до повторення блоків.

**Формат: цифрова + візуальна (рекомендації 2025–2026)**

Обираємо інструмент, який:
- безкоштовний або дуже дешевий на старті
- дозволяє спільне редагування без центру
- підтримує шаблони / бази даних / теги
- працює офлайн або з хорошим мобільним доступом
- легко масштабувати (від 10 до 1000+ вузлів)

**Найкращі варіанти інструментів (з порівнянням)**

| Варіант | Тип | Переваги для EME | Недоліки | Вартість | Рекомендація для старту |
|---------|-----|------------------|----------|----------|--------------------------|
| **Notion** (база даних + сторінки) | Хмарний, колаборативний | Шаблони, фільтри, сортування, ембед відео/скрінів, красивий вигляд, мобільний додаток, гостьовий доступ без акаунтів | Повністю хмарний (залежність від сервера), безкоштовний ліміт ~1000 блоків на робочий простір | Безкоштовно для особистих/малих груп, потім ~€8/міс на користувача | **Найкращий стартовий вибір** — швидко, красиво, всі знають |
| **Google Sheets / Google Docs** + шаблон | Таблиця + документи | 100% безкоштовно, офлайн-доступ, легко експортувати, фільтри/сортування | Менш візуально привабливо, не ідеально для довгих текстів | Безкоштовно | Якщо хочеш максимальну простоту та нуль витрат |
| **Obsidian + Git / Obsidian Publish / Sync** | Локальний Markdown + граф | Повністю офлайн, приватність, граф зв’язків (візуалізація емерджентності), плагіни для баз даних | Потрібен Git або платний Sync для спільного редагування, крутіша крива навчання | Безкоштовно (Sync ~€5/міс) | Для тех-вузлів, хто хоче максимальну незалежність |
| **Logseq** (open-source outliner) | Локальний + граф | Щоденні нотатки + запити, відкритий код, сильна спільнота | Слабше колаборативне редагування без плагінів | Безкоштовно | Якщо багато хто вже користується Logseq/Obsidian |
| **Discord + форум-канали + боти** або **Telegram + pinned/канал** | Чат + пін | Швидко, всі вже там, боти для тегів/пошуку | Не структуровано, важко шукати старі пости | Безкоштовно | Перехідний варіант, поки не буде окремої дошки |

**Рекомендація для EME на 2025–2026: Почніть з Notion**
(якщо група >20–30 людей — це найшвидший і найвізуальніший спосіб запустити дошку досвіду. Більшість людей вже знають Notion, шаблони роблять реплікацію легкою.)

**Структура Дошки досвіду в Notion (шаблон бази даних)**

Створюємо одну базу даних (Database) типу **Table / Gallery / Board** з такими властивостями (properties):

- Назва практики (Title) — короткий заголовок, наприклад: «Швидка допомога з резюме за 15 хв»
- Тип (Select): Допомога онлайн / Офлайн-зустріч / Шаблон тексту / Збір ресурсів / Подія / Інше
- Рівень складності (Select): 1–5 хв / 15–30 хв / 1–2 години / День+
- Автор вузла (Person або Text) — хто поділився
- Дата додавання (Date)
- Теги (Multi-select): #робота #здоровя #переїзд #техдопомога #емоційна #для-нових-вузлів тощо
- Результат (Text або Select): Успіх / Частковий успіх / Урок з помилки
- Короткий опис (Text) — 2–4 речення: що робив, для кого, результат
- Шаблон для повторення (Text або Toggle) — покроковий рецепт (копіюй-встав)
- Посилання / файли (Files & media) — скріншоти, гугл-доки, pdf, відео
- Уроки / що покращити (Text) — що не спрацювало, чому, як уникнути
- Лінки на подібні практики (Relation) — зв’язок з іншими записами в тій самій базі

**Візуальні режими перегляду (Views) в Notion:**

1. **Gallery** — картки з фото/іконками (найкрасивіше для мотивації)
2. **Board** — по типу або складності (як Trello)
3. **Table** — повний список для пошуку
4. **Timeline** — хронологія зростання мережі
5. **List з фільтром #для-нових-вузлів** — стартер-пак для новачків

**Процес додавання (з Протоколу взаємодії):**

- Зробив корисну дію → за 2–5 хв заповнюєш шаблон у базі (є кнопка «New» + шаблон)
- Додаєш #EMEдосвід у чаті + посилання на запис
- Щотижня/щомісяця хтось (будь-хто) робить «Топ-5 практик тижня» — постить у загальний канал

**Приклад запису (як виглядатиме картка):**

**Швидка допомога з резюме за 15 хв**
Тип: Допомога онлайн
Складність: 15–30 хв
Теги: #робота #для-нових-вузлів
Результат: Успіх (3 людини отримали запрошення)
Шаблон:
1. Запитай вакансію та поточне резюме
2. Порівняй ключові слова
3. Додай/перефразуй 3–5 пунктів під вакансію
4. Надішли версію + пояснення змін
Урок: коротше пояснення змін — краще сприймається

Це забезпечує **самореплікацію**: новий вузол заходить → фільтрує «для-нових-вузлів» → копіює шаблон → робить дію → додає свій результат → мережа вчиться."""),

            "support": ("Підтримка вузлів", """Документ про підтримку вузлів EME
(Колективна турбота — основа стійкості мережі)

EME — це мережа, де вузли не вигорають, бо підтримка один одного вбудована в систему.
Ми не герої, ми — частина живого організму. Якщо вузол виснажується — слабшає вся мережа. Тому ми створюємо механізми, які захищають учасників, зберігають ресурси та дозволяють системі працювати довго й стабільно.

1. Ресурси для відновлення (час, енергія, знання)

- **Право на паузу без провини**
  Будь-який вузол може взяти перерву (день, тиждень, місяць) без пояснень і без відчуття, що «підводить». Просто пише в чат: «Беру паузу» або «Потрібен відпочинок» — і це нормально.

- **Щоденні/щотижневі відновлювальні практики**
  Вбудовуємо в Кодекс вузла:
  - Мінімум 1 день на тиждень без будь-яких активностей EME.
  - Регулярно: сон, рух, хобі, природа, час з близькими (не для мережі, а для себе).
  - Колективні рекомендації: короткі медитації/дихальні вправи, списки «речей, які мене заряджають» (обмінюємося в чаті).

- **Ресурси знань про відновлення**
  У Дошці досвіду окремий розділ/тег #EMEвідновлення:
  - Шаблони «Як я вийшов з вигорання»
  - Списки безкоштовних ресурсів (апки для медитації, подкасти, статті)
  - Колективні рекомендації: книги/відео про sustainable activism, collective care, burnout prevention.

- **Матеріальна підтримка (якщо потрібно)**
  Якщо вузол у кризі (фінансовій, емоційній) — може анонімно/відкрито попросити: «Потрібна допомога з [конкретно]». Мережа реагує за принципом «give what you can, take what you need».

2. Методи контролю навантаження

- **Правило «не більше, ніж можу»**
  Кожен вузол сам визначає свій ліміт:
  - Скільки дій 1/1 на день (може бути 1, а не обов’язково більше).
  - Скільки часу на тиждень (наприклад, 2–5 годин max).
  - Якщо перевищив — сигналізує собі: «Забагато, зменшую».

- **Buddy-система або «пара підтримки»**
  Бажано мати 1–2 «бадді» (близьких вузлів), з якими:
  - Щотижня короткий чек-ін: «Як твій ресурс зараз? 1–10».
  - Якщо хтось падає нижче 4–5 — бадді нагадує про паузу, пропонує допомогу або бере на себе частину дій.

- **Ротація ролей**
  У локальних групах/подіях: ролі (ведучий, нотатки, модерація чату) міняються щотижня/щомісяця. Ніхто не «несе» все на собі постійно.

- **Сигнали тривоги в мережі**
  Якщо бачиш, що вузол пише частіше «вигорання», «важко», «не встигаю» — пиши приватно: «Бачу, що тобі зараз непросто. Чим можу підтримати? Можливо, пауза?». Без тиску, без суджень.

3. Канали взаємопідтримки

- **Загальний чат/канал — «Сигнал SOS»**
  Окремий канал або тег #EMEпідтримка або #потрібнадопомога:
  - Пиши: «Емоційно виснажений», «Потрібно виговоритися», «Фінансова скрута».
  - Відповідь: хто може — пропонує час, слово, ресурс. Анонімно теж можна.

- **Голосові кола підтримки**
  Щотижня/щомісяця: онлайн-коло «Перевірка ресурсу» (30–60 хв).
  Формат: кожен по черзі каже рівень енергії + що потрібно. Решта слухає, пропонує підтримку.

- **Локальні пари/малі групи**
  У місті/регіоні: створюйте малі чати 3–6 людей для глибшої підтримки (щоденні чек-іни, спільні прогулянки, «meal train» — коли хтось у кризі, інші приносять їжу/допомагають).

- **Колективна турбота про події**
  Перед великою подією/збором: перевіряємо «Хто втомлений? Хто бере паузу?».
  Після: обов’язковий «розбір + подяка + відпочинок».

Одна фраза, яку повторюємо:
«Мережа сильна, коли вузли живі. Турбота про себе — це турбота про всіх. Турбота про іншого — це турбота про себе.»

EME захищає учасників не правилами «зверху», а культурою:
- Нормально просити про допомогу.
- Нормально відмовляти.
- Нормально відпочивати.

Це робить нас стійкими.
Разом ми не просто виживаємо — ми виникаємо сильнішими."""),
            
            "expansion": ("План розширення", """План розширення мережі EME
(версія 1.0 — для самореплікації без центру)

Мета: мережа росте емерджентно — з незалежних дій вузлів, без центрального керівництва.
Кожен вузол може запускати розширення сам, використовуючи тільки доступні інструменти (чат, соцмережі, друзі, локальний простір).

1. Залучення нових вузлів
(як запускати хвилю запрошень без спаму)

Крок 1. Особисте запрошення (найефективніше, 80% росту)
- Щодня/щотижня: запрошуй 1–3 людей з твого кола (друзі, колеги, сусіди, онлайн-знайомі).
- Шаблон повідомлення:
  «Привіт! Я в EME — мережі, де щодня робимо маленькі дії підтримки один одному. Це допомагає вийти з ізоляції «робота-дом». Хочеш глянути маніфест? [посилання] Якщо сподобається — просто напиши в чат: «Хочу бути вузлом» — і ти вже в мережі.»
- Після запрошення: додай людину в загальний чат + надішли посилання на Кодекс вузла.

Крок 2. Вірусний контент (для ширшого охоплення)
- Пости в соцмережах (Instagram, Facebook, Telegram-канали, X):
  - Сторіз/пост з твоєю щоденною дією + #EME1на1 + заклик: «Зроби свою дію сьогодні — тегни мене, і я додам тебе в чат EME».
  - Короткі відео/тексти: «Як я допоміг незнайомцю за 5 хв — і це запустило ланцюжок».
- Хештеги: #EMEразом #EMEвузол #1діяна1день #людидлялюдей
- Якщо пост набирає охоплення — хтось інший копіює шаблон і робить свій.

Крок 3. Автоматичний онбординг
- У чаті/каналі: pinned-повідомлення з маніфестом + Кодексом + Протоколом + інструкцією: «Щоб стати вузлом — просто напиши: «Привіт, я [ім'я]. Хочу бути вузлом EME». Ми тебе додамо».
- Немає модерації: хто написав — той вже вузол.

2. Організація локальних та онлайн-активностей
(щоб мережа відчувалася живою, без «центральних» подій)

Крок 1. Локальні зустрічі (офлайн-вузли)
- Шаблон події: «EME-коло» (1–2 години, 3–10 людей).
  - Місце: парк, кав’ярня, коворкінг, квартира.
  - Структура:
    1. Коло знайомства (2 хв на людину: «Що мене привело в EME?»)
    2. Обмін діями тижня (кожен ділиться 1 успіхом/уроком)
    3. Планування: «Чим можемо допомогти один одному найближчим часом?»
    4. Закінчення: кожен запрошує 1 людину на наступне коло.
- Як запустити: будь-який вузол пише в чат: «Запускаю EME-коло у [місто/район] [дата/час]. Хто з нами?»
- Локальна копія: після зустрічі — короткий пост у загальному чаті з фото/уроками + шаблон для повторення в іншому місті.

Крок 2. Онлайн-активності (щотижневі/щомісячні)
- Голосові чати (Telegram/Discord): «EME-година підтримки» — тема: «Що тебе зараз турбує? Чим можемо допомогти?»
- Шаблон: «Запускаю онлайн-коло в неділю 20:00. Тема: [наприклад, вигорання]. Приєднуйтесь за посиланням».
- Інші формати: спільний перегляд фільму + обговорення, Q&A-сесія, «швидка допомога» (кожен ставить запит — інші відповідають за 2 хв).
- Розширення: хто брав участь — запускає своє коло в своєму часовому поясі/місті.

3. Створення локальних копій практик
(щоб практики дублювалися в нових містах/групах)

Крок 1. Використання Дошки досвіду
- Новий вузол заходить → фільтрує «для-нових-вузлів» або «локальні події».
- Копіює шаблон: завантажує маніфест, Кодекс, Протокол, Дошку як копію (Notion: Duplicate) або створює свій Google Doc/Telegram-канал.
- Додає свій локальний чат: «EME [Місто/Район]» — і запрошує перших людей.

Крок 2. Шаблон запуску локальної мережі
1. Створи чат/канал з назвою «EME [твоє місто/регіон]».
2. Запини: маніфест + Кодекс + Протокол + посилання на загальну Дошку досвіду.
3. Зроби першу дію: опублікуй свою щоденну допомогу + запроси 3–5 знайомих.
4. Запусти перше коло/подію за шаблоном вище.
5. Фіксуй у загальній Дошці: «Запустив локальну групу в [місто] — ось що спрацювало».

Крок 3. Моніторинг росту (без центру)
- Кожен вузол раз на місяць постить у загальний канал: «Мій внесок у розширення: +X нових вузлів, +1 подія».
- Це створює соціальний доказ і мотивує інших.

Одна фраза-пам’ятка для всіх вузлів:
«Я запускаю розширення у своєму колі — мережа росте сама. Моя дія + копіювання шаблону = нові вузли в новому місті.»

EME — не організація, а процес. Кожен вузол — це насіння нової мережі. Розширюйся там, де ти є. Це лише початок.""")
        }

        for slug, (title, content) in seed_content.items():
            page = Page.query.filter_by(slug=slug).first()
            if not page:
                page = Page(title=title, content=content, slug=slug)
                db.session.add(page)
            else:
                # Force update content in case it was truncated/old
                page.title = title
                page.content = content
        
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
