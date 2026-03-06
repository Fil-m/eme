import os
import socket
import subprocess
import sys

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        return result.stdout.strip() if result.returncode == 0 else ""
    except:
        return ""

def setup_ssl(mkcert_path="mkcert"):
    local_ip = get_local_ip()
    
    # Check if certificates exist
    if os.path.exists("cert.pem") and os.path.exists("key.pem"):
        return True

    # Check if mkcert is accessible
    mkcert_check = run_cmd(f'"{mkcert_path}" --version')
    if not mkcert_check:
        print("[!] mkcert binary not found at " + mkcert_path)
        return False

    # Generate certificates
    print(f"🎫 Generating trusted SSL certificates for {local_ip}...")
    run_cmd(f'"{mkcert_path}" -cert-file cert.pem -key-file key.pem localhost 127.0.0.1 {local_ip}')
    
    return os.path.exists("cert.pem") and os.path.exists("key.pem")

if __name__ == "__main__":
    # Known winget path for this environment
    path = "C:\\Users\\TRS\\AppData\\Local\\Microsoft\\WinGet\\Packages\\FiloSottile.mkcert_Microsoft.Winget.Source_8wekyb3d8bbwe\\mkcert.exe"
    if not os.path.exists(path):
        path = "mkcert"
        
    if setup_ssl(path):
        print("OK: SSL Provisioned")
    else:
        sys.exit(1)
