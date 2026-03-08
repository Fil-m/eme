import os
import requests
import zipfile
import shutil
import io
from django.conf import settings

def download_and_update_from_zip(repo_url):
    """
    Downloads the repository as a ZIP from GitHub and extracts it over the current BASE_DIR.
    repo_url example: https://github.com/Fil-m/eme.git
    """
    if not repo_url.endswith('.git'):
        return False, "Invalid repository URL"
    
    # Convert git URL to zip URL: https://github.com/Fil-m/eme/archive/refs/heads/main.zip
    base_repo = repo_url.replace('.git', '')
    zip_url = f"{base_repo}/archive/refs/heads/main.zip"
    
    try:
        response = requests.get(zip_url, timeout=30)
        if response.status_code != 200:
            return False, f"Failed to download ZIP: {response.status_code}"
        
        # Load ZIP into memory
        z = zipfile.ZipFile(io.BytesIO(response.content))
        
        # GitHub ZIPs have a top-level folder like 'eme-main'
        top_folder = z.namelist()[0].split('/')[0]
        
        # Extract to a temp location first
        temp_extract_path = os.path.join(settings.BASE_DIR, 'tmp_update')
        if os.path.exists(temp_extract_path):
            shutil.rmtree(temp_extract_path)
        os.makedirs(temp_extract_path)
        
        z.extractall(temp_extract_path)
        source_content = os.path.join(temp_extract_path, top_folder)
        
        # Copy files over BASE_DIR
        for item in os.listdir(source_content):
            s = os.path.join(source_content, item)
            d = os.path.join(settings.BASE_DIR, item)
            
            # Skip some files/dirs that shouldn't be overwritten on mobile
            if item in ['db.sqlite3', 'media', 'mobile', 'venv', '.env']:
                continue
                
            if os.path.isdir(s):
                if os.path.exists(d):
                    # For directories, we might want to merge or delete/replace
                    # Simple approach: remove and replace (safest for .vue components)
                    if item == 'static':
                        # Merge static/components specifically?
                        pass 
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
        
        # Cleanup
        shutil.rmtree(temp_extract_path)
        
        return True, "Систему успішно оновлено через ZIP!"
        
    except Exception as e:
        return False, f"Помилка оновлення через ZIP: {str(e)}"
