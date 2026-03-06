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
        self.known_peers = set() # Persistent IPs we've seen before
        self.running = False
        self.node_name = getattr(settings, 'EME_NODE_NAME', socket.gethostname())

    def _active_network_scan(self):
        """Proactively scans common local IPs if no nodes are seen via UDP."""
        import requests
        
        # Get local IP base (e.g. 192.168.1)
        base_ip = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            base_ip = ".".join(local_ip.split(".")[:-1])
            s.close()
        except:
            pass

        while self.running:
            if not self.nodes and base_ip:
                print(f"[Discovery] Active scan started on subnet {base_ip}.0/24")
                # We skip 127.0.0.1 and common routers/broadcasts
                # To avoid blocking, we use a thread pool or just a few common ones first
                # For now, let's just try 5-10 IPs around our own or common ones
                # or just the whole range slowly
                for i in range(1, 255):
                    if not self.running or self.nodes: break
                    target_ip = f"{base_ip}.{i}"
                    if target_ip in self.known_peers: continue # Skip if already checked by fallback
                    
                    try:
                        # Fast ping-like check
                        url = f"http://{target_ip}:8000/api/profiles/me/"
                        requests.get(url, timeout=0.1) # Extemely fast timeout for scanning
                    except:
                        pass
                    # Small sleep between pings to avoid flooding
                    time.sleep(0.01)
            
            time.sleep(60) # Scan every minute if empty

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._broadcast_presence, daemon=True).start()
        threading.Thread(target=self._listen_for_nodes, daemon=True).start()
        threading.Thread(target=self._direct_ping_fallback, daemon=True).start()
        threading.Thread(target=self._active_network_scan, daemon=True).start()
        print(f"EME Mesh Discovery started on port {self.port}")

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
                
                # Try all possible broadcast addresses
                broadcast_addrs = ['<broadcast>', '255.255.255.255']
                
                # Try to find local subnet broadcast (e.g. 192.168.1.255)
                try:
                    import subprocess
                    import re
                    # Simple hack to get possible broadcast addresses on Linux/Android and Windows
                    if os.name == 'nt':
                        output = subprocess.check_output("ipconfig", shell=True).decode('cp866')
                        matches = re.findall(r"IPv4 Address.*: ([\d\.]+)", output)
                        for m in matches:
                            parts = m.split('.')
                            if len(parts) == 4:
                                broadcast_addrs.append(f"{parts[0]}.{parts[1]}.{parts[2]}.255")
                    else:
                        output = subprocess.check_output("ifconfig", shell=True).decode('utf-8')
                        matches = re.findall(r"broadcast ([\d\.]+)", output)
                        broadcast_addrs.extend(matches)
                except:
                    pass
                
                # Remove duplicates and send
                for addr in set(broadcast_addrs):
                    try:
                        sock.sendto(message, (addr, self.port))
                    except:
                        pass
                        
            except Exception as e:
                print(f"Discovery broadcast error: {e}")
            time.sleep(10)

    def broadcast_sync_event(self, obj_type, sync_id):
        """Sends a UDP broadcast about a new object that needs to be synced."""
        if not self.running:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            data = {
                'action': 'sync',
                'type': obj_type,
                'sync_id': str(sync_id),
                'name': self.node_name,
                'ts': time.time()
            }
            message = json.dumps(data).encode('utf-8')
            # Send to generic broadcast
            sock.sendto(message, ('<broadcast>', self.port))
            # Also try to be more specific if possible
            sock.sendto(message, ('255.255.255.255', self.port))
        except Exception as e:
            print(f"Sync broadcast error: {e}")

    def _listen_for_nodes(self):
        """Listens for UDP broadcasts from other nodes."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('', self.port))
        except Exception as e:
            print(f"UDP listener failed to bind on port {self.port}: {e}")
            return
        
        while self.running:
            try:
                data, addr = sock.recvfrom(2048)
                ip = addr[0]
                
                # Simple check for self IP
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.settimeout(0)
                    s.connect(("10.254.254.254", 1))
                    own_ip = s.getsockname()[0]
                    s.close()
                    if ip == own_ip:
                        continue
                except:
                    pass

                payload = json.loads(data.decode('utf-8'))
                
                # Handle discovery pings
                if payload.get('type') == 'eme_discovery':
                    remote_name = payload.get('name', 'Unknown')
                    print(f"[Discovery] Received from {remote_name} at {ip}")
                    
                    # If this is the FIRST time we see this node recently, trigger catchup
                    if ip not in self.nodes or time.time() - self.nodes[ip].get('last_seen', 0) > 60:
                        print(f"[Discovery] Node {remote_name} ({ip}) is new/reconnected. Triggering catchup...")
                        threading.Thread(target=self._trigger_catchup, args=(ip,), daemon=True).start()
                        
                    self.nodes[ip] = {
                        'name': remote_name,
                        'last_seen': time.time()
                    }
                    self.known_peers.add(ip)
                    
                # Handle sync events
                elif payload.get('action') == 'sync':
                    obj_type = payload.get('type')
                    sync_id = payload.get('sync_id')
                    remote_name = payload.get('name', 'Unknown')
                    print(f"[SyncEvent] Received {obj_type} ({sync_id}) from {remote_name} ({ip})")
                    threading.Thread(target=self._pull_sync_data, args=(ip, obj_type, sync_id), daemon=True).start()

            except Exception as e:
                # Silently ignore malformed packets, but you could print for debug
                # print(f"UDP Packet Error: {e}")
                pass

    def _pull_sync_data(self, source_ip, obj_type, sync_id):
        """Background thread to pull and save data from another node."""
        from network.sync_service import pull_and_save_object
        pull_and_save_object(source_ip, obj_type, sync_id)

    def _trigger_catchup(self, source_ip):
        """Background thread to catch up with missed events."""
        from network.sync_service import catchup_with_node
        from network.models import Node
        node = Node.objects.filter(ip_address=source_ip).first()
        last_sync = node.last_sync_at if node else None
        catchup_with_node(source_ip, last_sync)

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

    def _direct_ping_fallback(self):
        """Attempts to ping known peers directly via HTTP if UDP is restricted."""
        # Initial load from DB
        try:
            from network.models import Node
            for node in Node.objects.all():
                if node.ip_address:
                    self.known_peers.add(node.ip_address)
        except:
            pass

        while self.running:
            import requests
            peers = list(self.known_peers)
            for ip in peers:
                # If we haven't seen them via UDP in the last 15 seconds, try HTTP
                if ip not in self.nodes or time.time() - self.nodes[ip]['last_seen'] > 15:
                    try:
                        # Direct heartbeat/discovery check
                        # We hit profiles/me/ but expect a 401/403 since we have no token.
                        # However, a 401/403 MEANS THE SERVER IS ALIVE at this IP.
                        url = f"http://{ip}:8000/api/profiles/me/"
                        res = requests.get(url, timeout=3)
                        
                        # Any response from the EME port (even 401/403) means the node is reachable
                        if res.status_code in [200, 401, 403]:
                            self.nodes[ip] = {
                                'name': 'FoundNode', # We can't get name without auth, but we see the IP
                                'last_seen': time.time()
                            }
                            print(f"[Discovery] Re-discovered via Direct HTTP (status {res.status_code}): {ip}")
                    except Exception:
                        pass
            time.sleep(20) # Ping every 20 seconds if needed

# Global instance
discovery_service = MeshDiscovery()
