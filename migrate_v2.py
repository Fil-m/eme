import sqlite3

import os

def migrate():
    db_path = os.path.join('instance', 'eme.db')
    if not os.path.exists(db_path):
        db_path = 'eme.db' # fallback
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Migrating nodes...")
    try:
        cursor.execute('ALTER TABLE nodes ADD COLUMN public_key TEXT')
        print("Added public_key to nodes")
    except sqlite3.OperationalError as e:
        print(f"Nodes update: {e}")

    print("Migrating actions...")
    try:
        cursor.execute('ALTER TABLE actions ADD COLUMN signature TEXT')
        print("Added signature to actions")
    except sqlite3.OperationalError as e:
        print(f"Actions update: {e}")

    print("Creating blobs table...")
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blobs (
                id TEXT PRIMARY KEY,
                data BLOB NOT NULL,
                mime_type TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Created blobs table")
    except Exception as e:
        print(f"Blobs creation: {e}")

    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
