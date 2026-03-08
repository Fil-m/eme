import os
import zipfile
import shutil

def bundle_core(source_dir, output_file):
    exclude_dirs = {
        '.git', 'venv', '__pycache__', 'dist', 'media', '.agent', 
        '.pytest_cache', '.vscode', '.idea', 'node_modules', 'mobile', 'build'
    }
    exclude_files = {
        'db.sqlite3', 'ai.sqlite3', 'game.sqlite3', 'kanban.sqlite3', 
        'kb.sqlite3', 'mafia.sqlite3', 'media.sqlite3', 'social.sqlite3',
        'utils.sqlite3', 'server.log', 'out.log', 'test.zip'
    }
    exclude_extensions = {'.pyc', '.pyo', '.pyd', '.bak', '.swp'}

    print(f"Bundling core from: {source_dir}")
    print(f"Target: {output_file}")

    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Фільтруємо папки
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files:
                    continue
                if any(file.endswith(ext) for ext in exclude_extensions):
                    continue
                
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                
                zipf.write(full_path, rel_path)
                # print(f"  + {rel_path}")

    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"Done! Core size: {size_mb:.2f} MB")

if __name__ == "__main__":
    current_dir = os.getcwd()
    dist_dir = os.path.join(current_dir, 'dist')
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)
    
    bundle_file = os.path.join(dist_dir, 'eme_mobile_core.zip')
    bundle_core(current_dir, bundle_file)
