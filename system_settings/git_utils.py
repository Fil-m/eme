import os
import subprocess
import tempfile
import shutil
from django.conf import settings

def run_git(args, cwd=None):
    if cwd is None:
        cwd = settings.BASE_DIR
        
    # Robustness: Remove index.lock if it exists (prevents fatal errors)
    lock_path = os.path.join(cwd, '.git', 'index.lock')
    if os.path.exists(lock_path):
        try:
            os.remove(lock_path)
        except:
            pass
            
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def push_app_to_git(draft):
    """
    Creates a branch for the app and pushes the component file.
    Does NOT touch the main project directory branch.
    Operates in a temporary clone to ensure 100% stability of the live site.
    """
    component_name = draft.component_name
    branch_name = f"apps/{component_name.lower().replace('emegenerated', '')}"
    file_rel_path = os.path.join('static', 'components', f"{component_name}.vue")
    
    # 1. Get the remote URL
    success, remote_url = run_git(['remote', 'get-url', 'origin'])
    if not success:
        return False, "Could not get git remote URL"
    remote_url = remote_url.strip()

    # 2. Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="eme_git_push_")
    
    try:
        # 3. Clone only the necessary commit/branch structure (shallow clone)
        # We use --no-checkout to avoid downloading all files immediately
        subprocess.run(['git', 'clone', '--depth', '1', '--no-checkout', remote_url, temp_dir], check=True, capture_output=True)
        
        # 4. Check if branch exists on remote
        success, _ = run_git(['ls-remote', '--heads', 'origin', branch_name], cwd=temp_dir)
        
        if branch_name in _:
            # Branch exists, fetch it and checkout
            subprocess.run(['git', 'fetch', 'origin', branch_name, '--depth', '1'], cwd=temp_dir, check=True, capture_output=True)
            subprocess.run(['git', 'checkout', branch_name], cwd=temp_dir, check=True, capture_output=True)
        else:
            # Branch doesn't exist, create it from the default HEAD
            # We need at least some commit to start from, so we fetch main/master
            subprocess.run(['git', 'fetch', 'origin', 'main', '--depth', '1'], cwd=temp_dir, check=False)
            subprocess.run(['git', 'checkout', '-b', branch_name], cwd=temp_dir, check=True, capture_output=True)

        # 5. Ensure target directory exists in temp clone
        full_file_path = os.path.join(temp_dir, file_rel_path)
        os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
        
        # 6. Write the component code
        with open(full_file_path, 'w', encoding='utf-8') as f:
            f.write(draft.vue_code)
            
        # 7. Commit and Push
        # Set dummy user if not configured (common in some environments)
        subprocess.run(['git', 'config', 'user.email', 'eme-os@ai.bot'], cwd=temp_dir, check=True)
        subprocess.run(['git', 'config', 'user.name', 'EME AI Builder'], cwd=temp_dir, check=True)
        
        subprocess.run(['git', 'add', file_rel_path], cwd=temp_dir, check=True)
        commit_res = subprocess.run(['git', 'commit', '-m', f"Publish AI app: {draft.name}"], cwd=temp_dir, capture_output=True, text=True)
        
        # Always push, even if commit says "nothing to change" (just in case)
        push_res = subprocess.run(['git', 'push', 'origin', branch_name], cwd=temp_dir, capture_output=True, text=True)
        
        if push_res.returncode != 0:
            return False, f"Git push failed: {push_res.stderr}"
            
        return True, f"Успішно опубліковано в гілку {branch_name} (Out-of-tree push)"
        
    except Exception as e:
        return False, f"Git operation failed: {str(e)}"
    finally:
        # 8. Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def auto_update_sync():
    """
    Runs git pull to keep the system updated.
    """
    success, out = run_git(['pull', 'origin', 'main'])
    return success, out
