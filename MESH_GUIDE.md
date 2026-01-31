# EME Mesh Network Guide

This guide explains how to create a local mesh network and sync data between EME nodes without internet.

## Table of Contents
1. [Creating a Hotspot (Android)](#creating-a-hotspot-android)
2. [Finding Your IP Address](#finding-your-ip-address)
3. [Connecting Others](#connecting-others)
4. [Syncing Data](#syncing-data)
5. [How Mesh Works](#how-mesh-works)

---

## Creating a Hotspot (Android)

To allow others to connect to your node, create a mobile hotspot:

1. Open **Settings** on your Android device
2. Navigate to **Network & Internet** → **Hotspot & Tethering**
3. Enable **Wi-Fi Hotspot**
4. Set a network name and password (e.g., "EME_MESH" / "eme12345")
5. Leave hotspot running

**Note:** Your node must be running (`python app.py`) while hotspot is active.

---

## Finding Your IP Address

Once hotspot is enabled and EME is running, find your local IP:

### Method 1: Check Terminal Output
When you run `python app.py`, the terminal shows:
```
* Running on http://0.0.0.0:5000
* Running on http://10.117.186.169:5000
```
The second line shows your **local IP** (e.g., `10.117.186.169`).

### Method 2: Manual Check in Termux
```bash
ifconfig
```
or
```bash
ip addr show wlan0
```

Look for a line like:
```
inet 192.168.43.1/24
```

Your IP is `192.168.43.1` (yours may differ: `10.x.x.x`, `192.168.x.x`, etc.).

---

## Connecting Others

### Step 1: Others Join Your Hotspot
People who want to sync with you should:
1. Connect to your Wi-Fi hotspot (e.g., "EME_MESH")
2. Enter the password you set

### Step 2: Others Access Your Node
Once connected to your hotspot, they open a browser and navigate to:
```
http://YOUR_IP:5000
```

For example:
```
http://192.168.43.1:5000
```

They'll see your EME interface and can browse your actions.

---

## Syncing Data

There are **two ways** to sync:

### Option 1: QR Code (Recommended)

This is the "touch devices to sync" method.

**On your node:**
1. Navigate to **SYNC** section
2. Your node displays a QR code with your address

**On their device:**
1. Click **📷 Scan QR**
2. Point camera at your QR code
3. Click **Run Sync**

Data syncs automatically. No duplicate entries (UUIDs prevent this).

### Option 2: Manual Address Entry

If QR scanning is unavailable:

1. Go to **SYNC** section
2. Enter peer address manually: `http://192.168.43.1:5000`
3. Click **Run Sync**

---

## How Mesh Works

### What is a Mesh Network?

In EME, every node is both a **server** and a **client**:
- **Server**: Your node hosts data that others can pull
- **Client**: Your node can pull data from others

There is **no central server**. Everyone holds a copy of the data they've synced.

### Transitive Sync (Gossip Protocol)

When you sync with a friend, you don't just get their actions — you get **everything they know**:

```
You ←→ Friend ←→ Their Friend
```

After syncing with "Friend", you'll have:
- Your own actions
- Friend's actions
- Actions Friend synced from "Their Friend"

This creates a **self-replicating network**. Information flows like a reef growing outward.

### Data Integrity

- Every action has a **unique UUID** → no duplicates
- Sync only pulls **new** data
- Database automatically merges without conflicts

### Offline First

Mesh works entirely over:
- **Local Wi-Fi** (hotspot)
- **Direct Wi-Fi** (peer-to-peer, advanced)
- **LAN** (router-based network)

**No internet required.** Data stays local until you choose to sync.

---

## Becoming a Seed Node

A **seed node** is simply a node that:
1. Runs most of the time
2. Has accumulated many synced actions
3. Serves as a "bookmark" for newcomers

To be a seed:
- Keep your node running
- Share your QR code at community gatherings
- Let people sync with you regularly

---

## Troubleshooting

### "Cannot connect to peer"
- Ensure peer's hotspot is active
- Verify you're connected to the same Wi-Fi
- Check firewall settings (rare on mobile)

### "Sync completed but no new data"
- You may already have all their actions
- Check action log timestamps

### "Data not updating"
- Refresh your browser
- Sync pulls data but doesn't auto-refresh UI

---

*EME — People for People*  
The mesh is alive. Join it.
