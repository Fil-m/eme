import sqlite3
import os

db_path = "instance/eme.db"
if not os.path.exists(db_path):
    db_path = "eme.db"

if not os.path.exists(db_path):
    print(f"Database file {db_path} not found. Nothing to migrate.")
    exit()

print(f"Using database: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Starting migration to Scrum v2.2...")

# 1. Create Projects table if missing
try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        category_id TEXT,
        creator_node_id TEXT NOT NULL,
        parent_id TEXT,
        status TEXT DEFAULT 'active',
        definition_of_done TEXT,
        created_at TEXT,
        FOREIGN KEY(category_id) REFERENCES action_types(id),
        FOREIGN KEY(creator_node_id) REFERENCES nodes(id),
        FOREIGN KEY(parent_id) REFERENCES projects(id)
    )
    """)
    print("- Created 'projects' table (if missing).")
    
    # Check for missing columns in projects
    cursor.execute("PRAGMA table_info(projects)")
    p_columns = [col[1] for col in cursor.fetchall()]
    if 'definition_of_done' not in p_columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN definition_of_done TEXT")
        print("- Added 'definition_of_done' to 'projects' table.")
    
except Exception as e:
    print(f"- Error creating/updating 'projects': {e}")

# 2. Update Actions table
try:
    # Check if columns already exist to avoid errors
    cursor.execute("PRAGMA table_info(actions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'project_id' not in columns:
        cursor.execute("ALTER TABLE actions ADD COLUMN project_id TEXT")
        print("- Added 'project_id' to 'actions' table.")
    
    if 'milestone_id' not in columns:
        cursor.execute("ALTER TABLE actions ADD COLUMN milestone_id TEXT")
        print("- Added 'milestone_id' to 'actions' table.")
        
    if 'assignee_node_id' not in columns:
        cursor.execute("ALTER TABLE actions ADD COLUMN assignee_node_id TEXT")
        print("- Added 'assignee_node_id' to 'actions' table.")
        
except sqlite3.OperationalError as e:
    print(f"- Error updating 'actions': {e}")

# 3. Create Milestones table
try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS milestones (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        deadline TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id)
    )
    """)
    print("- Created 'milestones' table.")
except Exception as e:
    print(f"- Error creating 'milestones': {e}")

# 4. Create Participations table
try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS participations (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        node_id TEXT NOT NULL,
        role TEXT DEFAULT 'member',
        created_at TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id),
        FOREIGN KEY(node_id) REFERENCES nodes(id)
    )
    """)
    print("- Created 'participations' table.")
except Exception as e:
    print(f"- Error creating 'participations': {e}")

conn.commit()
conn.close()
print("Migration completed successfully!")
