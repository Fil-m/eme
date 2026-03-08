import os
import subprocess
from django.conf import settings

def run_git(args, cwd=None):
    if cwd is None:
        cwd = settings.BASE_DIR
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
    Uses stashing to handle dirty working directory.
    """
    component_name = draft.component_name
    branch_name = f"apps/{component_name.lower().replace('emegenerated', '')}"
    file_path = os.path.join('static', 'components', f"{component_name}.vue")
    
    # 1. Stash any existing changes to system files to allow branch switching
    run_git(['stash', 'push', '-m', f"EME Temporary stash before pushing {draft.name}"])
    
    try:
        # 2. Ensure file is staged (if it was stashed, we might need a different approach, 
        # but usually new files are fine or we can just git checkout main -- file)
        
        # Actually, let's just use the current state of the file
        # 3. Create/Switch to branch
        success, out = run_git(['checkout', '-b', branch_name])
        if not success:
            success, out = run_git(['checkout', branch_name])
            if not success: return False, f"Git checkout failed: {out}"
        
        # 4. Bring the file from main if it's not there or updated
        run_git(['checkout', 'main', '--', file_path])
        
        # 5. Commit
        run_git(['add', file_path])
        run_git(['commit', '-m', f"Publish AI app: {draft.name}"])
        
        # 6. Push to origin
        success, out = run_git(['push', 'origin', branch_name])
        if not success:
            return False, f"Git push failed: {out}"
        
        return True, f"Успішно опубліковано в гілку {branch_name}"
        
    finally:
        # 7. Always return to main and restore stash
        run_git(['checkout', 'main'])
        run_git(['stash', 'pop'])

def auto_update_sync():
    """
    Runs git pull to keep the system updated.
    """
    success, out = run_git(['pull', 'origin', 'main'])
    return success, out
