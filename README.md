# EME — People for People
### An Emergent Network of Care — We Arise Together

![EME Concept](https://thumbs.dreamstime.com/b/vibrant-coral-reef-teeming-colorful-marine-life-under-sunlight-rays-creating-lively-underwater-scene-366816580.jpg)

**EME** (Experimental Mesh Environment) is a digital tool to support a human coral reef. It allows people to become "nodes" in a decentralized network of care, documenting small acts of kindness and syncing them offline without central servers.

> **"We don’t start with rules or a manifesto. We start with a wonder that already exists in nature."**

Every node is a server. Every node is a client. We grow horizontally, by ourselves.

## 🌊 The Philosophy
We are inspired by emergence. Like coral polyps, individually we are small, but together we act as a massive, resilient structure visible from space.

- **Help is normal**, not heroic.
- **Trust is practiced daily.**
- **Technology serves people.**
- **No center. No leaders.**

[Read the full Vision & Manifesto](./MANIFESTO.md)

## ✨ Features
- **Offline First**: Works entirely over Local LAN / Hotspots. No internet required.
- **P2P Sync**: "Touch" two devices to sync data (QR Code handshakes).
- **Knowledge Base**: Distributed markdown documentation system.
- **Action Logs**: Append-only log of all events (The "Experience Board").
- **Bilingual**: Fully localized for Ukrainian (UA) and English (EN).

## 📱 Rapid Install (Android / Termux)
Be the seed for a new network in your city.

1. Install **Termux** from F-Droid.
2. Run this command (or scan the QR code from another EME node):
   ```bash
   pkg update -y && pkg install python -y
   curl -O http://<EXISTING_NODE_IP>:5000/install.sh
   bash install.sh
   ```

## 💻 Manual Install (Windows / Linux)
1. **Clone & Install**:
   ```bash
   git clone https://github.com/Fil-m/eme.git
   cd eme
   pip install -r requirements.txt
   ```
2. **Run**:
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your browser.

## 🤝 How to Join & Contribute
**"No approval needed. You’re already a node."**

### For Users
1. **Become a Node**: Install the app.
2. **Practice 1/1**: Do 1 act of support daily. Log it in the app.
3. **Sync**: Meet another node, scan their QR, and share "memory".

### For Developers
We need your help to keep this "reef" healthy.
- **Code**: Python (Flask) + HTML/CSS (No complex build steps).
- **Design**: "Rich Aesthetics" — vibrant, organic, human.
- **Docs**: Translate content, improve guides.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for technical details.

## License
**MIT License**. Free to use, modify, and replicate.

---
*“This is just the beginning. Join us. Here. Now. By ourselves.”*
