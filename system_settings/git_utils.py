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
    """
    component_name = draft.component_name
    branch_name = f"apps/{component_name.lower().replace('emegenerated', '')}"
    file_path = os.path.join('static', 'components', f"{component_name}.vue")
    
    # 1. Ensure file is staged
    success, out = run_git(['add', file_path])
    if not success: return False, f"Git add failed: {out}"
    
    # 2. Commit (optional, might fail if no changes, so we ignore error)
    run_git(['commit', '-m', f"Publish AI app: {draft.name}"])
    
    # 3. Create/Switch to branch
    success, out = run_git(['checkout', '-b', branch_name])
    if not success:
        # If branch exists, just switch
        success, out = run_git(['checkout', branch_name])
        if not success: return False, f"Git checkout failed: {out}"
    
    # 4. Push to origin
    success, out = run_git(['push', 'origin', branch_name])
    if not success:
        return False, f"Git push failed: {out}. Check if remote 'origin' is configured and writable."
    
    # 5. Switch back to main (optional)
    run_git(['checkout', 'main'])
    
    return True, f"Successfully pushed to branch {branch_name}"

def auto_update_sync():
    """
    Runs git pull to keep the system updated.
    """
    success, out = run_git(['pull', 'origin', 'main'])
    return success, out
