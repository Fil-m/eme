import socket
import threading
import json
import time
from django.conf import settings

class MeshDiscovery:
    """Handles UDP broadcast for node discovery in local network."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MeshDiscovery, cls).__new__(cls)
                cls._instance._init_discovery()
        return cls._instance

    def _init_discovery(self):
        self.port = 54321
        self.nodes = {}  # {ip: {name, last_seen, ts}}
        self.running = False
        self.node_name = getattr(settings, 'EME_NODE_NAME', socket.gethostname())

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._broadcast_presence, daemon=True).start()
        threading.Thread(target=self._listen_for_nodes, daemon=True).start()
        print(f"📡 EME Mesh Discovery started on port {self.port}")

    def _broadcast_presence(self):
        """Sends UDP broadcast every 10 seconds."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        while self.running:
            try:
                data = {
                    'type': 'eme_discovery',
                    'name': self.node_name,
                    'ts': time.time()
                }
                message = json.dumps(data).encode('utf-8')
                sock.sendto(message, ('<broadcast>', self.port))
            except Exception as e:
                print(f"Discovery broadcast error: {e}")
            time.sleep(10)

    def _listen_for_nodes(self):
        """Listens for UDP broadcasts from other nodes."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.port))
        
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                ip = addr[0]
                
                # Try to get own IP to skip self
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    own_ip = s.getsockname()[0]
                    s.close()
                    if ip == own_ip:
                        continue
                except:
                    pass

                payload = json.loads(data.decode('utf-8'))
                if payload.get('type') == 'eme_discovery':
                    self.nodes[ip] = {
                        'name': payload.get('name'),
                        'last_seen': time.time()
                    }
            except Exception as e:
                pass

    def get_active_nodes(self):
        """Returns list of nodes seen in the last 30 seconds."""
        now = time.time()
        active = []
        # Clean up old nodes
        to_delete = []
        for ip, info in self.nodes.items():
            if now - info['last_seen'] < 30:
                active.append({
                    'ip': ip,
                    'name': info['name'],
                    'last_seen': info['last_seen']
                })
            else:
                to_delete.append(ip)
        
        for ip in to_delete:
            del self.nodes[ip]
            
        return active

# Global instance
discovery_service = MeshDiscovery()
