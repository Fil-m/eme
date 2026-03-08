import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import threading
import os
import sys
import time
import zipfile
import traceback
import io

class TogaLogStream(io.TextIOBase):
    def __init__(self, log_func):
        super().__init__()
        self.log_func = log_func
    def write(self, s):
        if s.strip():
            self.log_func(s)
        return len(s)

class EMEOSMobile(toga.App):
    def startup(self):
        try:
            # 1. Setup paths & state
            self.app_dir = self.paths.app
            self.data_dir = self.paths.data
            self.core_zip = os.path.join(self.app_dir, 'resources', 'eme_mobile_core.zip')
            self.core_dir = os.path.join(self.data_dir, 'eme_core')
            self.extract_marker = os.path.join(self.core_dir, '.extracted_at')
            self.desktop_mode = False
            self.current_port = 8000
            
            # 2. Main Window
            self.main_window = toga.MainWindow(title=self.formal_name)
            
            # 3. UI Components
            # IMPORTANT: Hide label and logs by default (flex=0) to give WebView full screen
            self.label = toga.Label("EME OS: Starting...", style=Pack(margin=2, font_size=8))
            self.log_area = toga.MultilineTextInput(readonly=True, style=Pack(flex=0, height=0, margin=0, font_size=7))
            self.webview_container = toga.Box(style=Pack(flex=1))
            
            self.main_box = toga.Box(
                children=[self.label, self.log_area, self.webview_container],
                style=Pack(direction=COLUMN)
            )
            self.main_window.content = self.main_box

            # 4. Commands (Menu)
            try:
                self.cmd_refresh = toga.Command(
                    self.refresh_webview,
                    label="Refresh Interface",
                    group=toga.Group.COMMANDS
                )
                self.cmd_toggle_logs = toga.Command(
                    self.toggle_logs,
                    label="Show/Hide Console",
                    group=toga.Group.COMMANDS
                )
                self.cmd_desktop_mode = toga.Command(
                    self.toggle_desktop_mode,
                    label="Switch to Desktop View",
                    group=toga.Group.COMMANDS
                )
                
                self.commands.add(self.cmd_refresh, self.cmd_toggle_logs, self.cmd_desktop_mode)
            except Exception as e:
                print(f"COMMAND SETUP FAILED: {e}")

            self.main_window.show()

            # Redirect output
            sys.stdout = TogaLogStream(self.log)
            sys.stderr = TogaLogStream(self.log)

            # Start Backend in Background
            threading.Thread(target=self.run_backend, daemon=True).start()

        except Exception as e:
            print(f"CRITICAL STARTUP ERROR: {e}")
            traceback.print_exc()

    def log(self, text):
        def _update():
            new_text = f"[{time.strftime('%H:%M:%S')}] {text.strip()}\n"
            self.log_area.value += new_text
            if len(self.log_area.value) > 8000:
                self.log_area.value = self.log_area.value[-5000:]
        
        if hasattr(self, 'loop'):
            self.loop.call_soon_threadsafe(_update)
        else:
            print(text)

    def refresh_webview(self, widget=None):
        if hasattr(self, 'webview'):
            self.log("Manual Refresh triggered.")
            self.webview.url = f"http://127.0.0.1:{self.current_port}?t={time.time()}"

    def toggle_logs(self, widget=None):
        def _toggle():
            # Toggle between hidden (flex=0) and visible (flex=1)
            if self.log_area.style.flex == 0:
                self.log_area.style.flex = 1
                self.log_area.style.height = 200 # Give it some height when visible
                self.log("Console expanded.")
            else:
                self.log_area.style.flex = 0
                self.log_area.style.height = 0
                self.log("Console collapsed.")
            self.main_box.refresh()
            
        self.loop.call_soon_threadsafe(_toggle)

    def toggle_desktop_mode(self, widget=None):
        self.desktop_mode = not self.desktop_mode
        if self.desktop_mode:
            self.cmd_desktop_mode.label = "Switch to Mobile View"
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        else:
            self.cmd_desktop_mode.label = "Switch to Desktop View"
            user_agent = None 
        
        if hasattr(self, 'webview'):
            self.log(f"Desktop Mode set to: {self.desktop_mode}")
            self.webview.user_agent = user_agent
            self.refresh_webview()

    def run_backend(self):
        try:
            self.log("Backend process started.")
            
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir, exist_ok=True)

            should_extract = False
            if not os.path.exists(os.path.join(self.core_dir, 'manage.py')):
                should_extract = True
            elif os.path.exists(self.core_zip):
                zip_mtime = os.path.getmtime(self.core_zip)
                marker_mtime = 0
                if os.path.exists(self.extract_marker):
                    marker_mtime = os.path.getmtime(self.extract_marker)
                
                if zip_mtime > marker_mtime:
                    self.log("Newer core bundle detected. Updating...")
                    should_extract = True

            if should_extract and os.path.exists(self.core_zip):
                self.log("Extracting/Updating core assets...")
                if os.path.exists(self.core_dir):
                    import shutil
                    try:
                        for item in os.listdir(self.core_dir):
                            if item.endswith('.sqlite3'): continue
                            item_path = os.path.join(self.core_dir, item)
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                            else:
                                os.remove(item_path)
                    except Exception as e:
                        self.log(f"Cleanup error: {e}")

                os.makedirs(self.core_dir, exist_ok=True)
                with zipfile.ZipFile(self.core_zip, 'r') as zip_ref:
                    zip_ref.extractall(self.core_dir)
                
                # Create/Update marker
                with open(self.extract_marker, 'w') as f:
                    f.write(str(time.time()))
            
            if self.core_dir not in sys.path:
                sys.path.insert(0, self.core_dir)
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eme.settings')
            
            import django
            django.setup()
            
            from django.core.management import call_command
            try:
                call_command('migrate', interactive=False)
            except Exception as e:
                self.log(f"Migration msg: {e}")

            self.server_ready = False
            def start_django():
                from django.core.servers.basehttp import run
                from django.core.handlers.wsgi import WSGIHandler
                from django.contrib.staticfiles.handlers import StaticFilesHandler
                import socket
                
                app = StaticFilesHandler(WSGIHandler())
                for port in range(8000, 8010):
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.bind(('127.0.0.1', port))
                        self.current_port = port
                        self.server_ready = True
                        run('127.0.0.1', port, app)
                        break
                    except OSError:
                        continue

            threading.Thread(target=start_django, daemon=True).start()

            waited = 0
            while not self.server_ready and waited < 15:
                time.sleep(1)
                waited += 1
            
            if self.server_ready:
                def show_webview():
                    url = f"http://127.0.0.1:{self.current_port}"
                    self.webview = toga.WebView(url=url, style=Pack(flex=1))
                    self.webview_container.add(self.webview)
                    self.label.text = f"EME OS — Online"
                    # Initial hide to ensure full screen
                    self.log_area.style.flex = 0
                    self.log_area.style.height = 0
                    self.log("Interface ready.")
                self.loop.call_soon_threadsafe(show_webview)
            else:
                self.log("Backend timeout.")

        except Exception:
            self.log(f"Startup crash: {traceback.format_exc()}")

def main():
    return EMEOSMobile()
