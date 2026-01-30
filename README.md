# EME Node (Experimental Mesh Environment)

**EME** is a peer-to-peer data replication system designed for offline environments. It runs on Android phones (Termux) and laptops, creating a resilient "knowledge web" without central servers.

Every node is a server. Every node is a client.

## Features
- **Offline First**: Works entirely over Local LAN / Hotspots. No internet required.
- **P2P Sync**: "Touch" two devices to sync data (QR Code handshakes).
- **Knowledge Base**: Distributed markdown documentation system.
- **Action Logs**: Append-only log of all events in the mesh.
- **Bilingual**: Fully localized for Ukrainian (UA) and English (EN).

## 📱 Rapid Install (Android / Termux)

1. Install **Termux** from F-Droid.
2. Run this command (or scan the QR code from another node):
   ```bash
   pkg update -y && pkg install python -y
   curl -O http://<EXISTING_NODE_IP>:5000/install.sh
   bash install.sh
   ```

## 💻 Manual Install (Windows / Linux)

1. **Clone & Install**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/eme.git
   cd eme
   pip install -r requirements.txt
   ```

2. **Run**:
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your browser.

## How it Works
- **Node+**: Any device can "replicate" itself to another device via `/replicate`.
- **Sync**: Devices discover each other manually (via IP/QR) and pull new "Actions" from peers.
- **Conflict Free**: All data uses UUIDs. Sync is additive (no overwrites, only new history).

## License
MIT License. Free to use and modify.
