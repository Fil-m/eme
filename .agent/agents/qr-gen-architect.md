# QR Code Generator: Kit Architect

> **Status**: Planning phase.
> **Scope**: d:\dev\eme\qr_generator\ (logic) + EmeQrGenerator.vue (UI)

## Context Tracker

| Component | Status | Responsibilities |
|-----------|--------|------------------|
| **Frontend UI** | [ ] | Input field, QR preview, download button. |
| **QR Logic** | [ ] | Client-side generation using qrcode library. |
| **Integration** | [ ] | Registration in Apps Store (Utilities). |

## Technical Notes
- **Library**: `qrcode` (SFC loader compatible).
- **Format**: SVG or Canvas for high quality.
- **Portability**: Must be lightweight for Termux/Mobile.
