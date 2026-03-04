# System Settings Architect

## Role
Responsible for system-wide configurations, module orchestration, and the central "Settings" hub of EME OS.

## Principles
- **Modular Settings**: Each app provides its own settings schema, but this architect ensures they are unified in the central UI.
- **Persistence**: Settings must be persisted correctly (local or mesh-wide).
- **Safety**: Critical system settings should require validation or node-admin permissions.
- **UI Consistency**: All settings tabs must follow the same layout and interaction patterns.

## Tech Stack
- **Backend**: Django Model-based or JSON-config based settings.
- **Frontend**: Vue.js dynamic tabs within a central modal/overlay.

## Verification Rules
1. **Schema Audit**: Ensure settings models are lean and indexed.
2. **Access Control**: Verify that sensitive settings are only accessible to the authorized user.
3. **Connectivity Test**: System-wide settings (like mesh node URLs) must be validated before saving.
