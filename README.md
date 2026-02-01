# EME — People for People

https://t.me/EME_chat 4 help

**EME** (Experimental Mesh Environment) — a decentralized care network. People help people. Technology serves people.

We build a world where:
- Help is normal, not heroic
- Trust is practiced daily  
- Every action matters
- The network grows horizontally, without a center

---
## Quick Start

### 📱 Android (Termux) — Recommended

**Important:** Install Termux only from [F-Droid](https://f-droid.org/), **NOT Google Play**.

✅ **What exactly to install in F-Droid:**
- 🔹 **Name:** Termux
- 🔹 **Description:** Terminal emulator with packages (by Fredrik Fornwall)

```bash
# One-line install from existing node:
curl -O http://<NODE_IP>:5000/install.sh && bash install.sh
```

> [!IMPORTANT]
> **When installing in Termux:** If you see questions like `What would you like to do about it?` or `(Y/I/N/O/D/Z)`, just press **Enter** (default). There may be several such questions.

**Or manual install:**
```bash
# 1. Update and install basics
pkg update -y && pkg upgrade -y
pkg install python git -y

# 2. Clone repository
git clone https://github.com/Fil-m/eme.git
cd eme

# 3. Install system dependencies (for image processing)
pkg install libjpeg-turbo zlib libpng freetype clang make libwebp -y

# 4. Install Python packages
pip install --upgrade pip wheel
LDFLAGS="-L$PREFIX/lib" CFLAGS="-I$PREFIX/include" pip install -r requirements.txt

# 5. Run
python app.py
```

Open on your phone: `http://127.0.0.1:5000`

### 💻 Windows / Linux

```bash
git clone https://github.com/Fil-m/eme.git
cd eme
pip install -r requirements.txt
python app.py
```

Open: `http://localhost:5000`

---

##  Creating a Mesh Network

To connect with others and sync data, see the detailed [Mesh Network Guide](./MESH_GUIDE.md).

Quick version:
1. Enable mobile hotspot on your Android
2. Others connect to your WiFi
3. Share your IP (shown in terminal) or QR code
4. Sync with "📷 Scan QR" or manual IP entry

---

## Philosophy

EME is inspired by nature — like coral polyps creating massive reefs. Individually small, together unstoppable.

- **Horizontality**: No center, no leaders
- **Transparency**: Open code, open data
- **Reality**: Works here and now, offline
- **Reproducibility**: Easy to replicate anywhere
- **Scientific & Iterative**: We create projects using the scientific method (hypotheses → tests → data) and implement through Scrum-like practices (iterations, daily synchronicities, retrospectives) so that everything grows organically and efficiently.
Read the full vision: [MANIFESTO.md](./MANIFESTO.md)

---

## Participation

We seek people who:
- Do small acts of care daily
- Believe in horizontal networks  
- Want to change the world locally and concretely

How to join:
1. **Run your node**
2. **Log 1 action daily**
3. **Sync with friends**
4. **Become part of the network**

Developers: See [CONTRIBUTING.md](./CONTRIBUTING.md)

---

## Troubleshooting

### Termux: `ModuleNotFoundError: No module named 'PIL'`

This means Pillow wasn't installed correctly. Run:

```bash
pkg install libjpeg-turbo zlib libpng freetype clang make libwebp -y
pip install --upgrade pip wheel
LDFLAGS="-L$PREFIX/lib" CFLAGS="-I$PREFIX/include" pip install Pillow
pip install qrcode[pil]
```

Verify:
```bash
python -c "from PIL import Image; print('Pillow OK')"
```

---

## License

**MIT License** — Free to use, modify, and replicate.

---

*"This is just the beginning. Join us. Here. Now. By ourselves."*
