# Clone Master: Kit Architect

> **Status**: Implementing selective archiving logic.
> **Scope**: d:\dev\eme\clone_master\

## Context Tracker

| Component | Status | Responsibilities |
|-----------|--------|------------------|
| **Backend API** | [/] | Zip generation, module discovery, Architect manifest creation. |
| **Frontend UI** | [ ] | Module selection checklist, download link management. |
| **Archive Logic** | [/] | Filter by `INSTALLED_APPS`, skip `venv`, `__pycache__`, `db.sqlite3`. |

## Module Map (Targetable for Cloning)
- `eme`: Core settings and shell.
- `profiles`: User management.
- `eme_nav`: Dynamic navigation.
- `eme_media`: Filesystem and gallery.
- `network`: Mesh and discovery.
- `clone_master`: Self-cloning capabilities.

## Technical Notes
- **Compression**: `zipfile.ZIP_DEFLATED`.
- **Architect Manifest**: Every clone includes a `CLONE_INFO.md` describing its content.
- **Safety**: Archives are generated in a temporary `clones/` directory and served via a dedicated endpoint.
