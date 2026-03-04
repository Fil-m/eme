# EME OS — Integrated Life & Work Management System

**EME OS** is a powerful, self-hosted platform designed for neurodivergent individuals to manage projects, track tasks, and build a digital ecosystem. It features deep integration with local LLMs (Ollama) for intelligent scaffolding and automation.

![EME OS UI](https://raw.githubusercontent.com/Fil-m/eme/main/static/css/screenshot_placeholder.png)

## 🚀 Key Features

*   **🪄 AI Assistant**: Automatically generate project roles and action plans based on your project description. Local LLM support via Ollama (llama3.2:3b).
*   **📋 Kanban Boards**: Manage projects across domains (Life, Business, Tech, Community) with priority-based drag-and-drop.
*   **👤 Profiles & XP**: Gamified experience with levels and activity tracking.
*   **🌍 Network Sync**: Built-in heartbeat system for distributed EME nodes.
*   **📦 Media Management**: Centralized gallery and collection system.

---

## 💻 Installation

### Windows (Recommended)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Fil-m/eme.git
    cd eme
    ```

2.  **Setup Environment**:
    We recommend using a virtual environment.
    ```bash
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Run with one click**:
    Just run `start.bat`. It will automatically:
    *   Launch **Ollama** server.
    *   Launch **EME Telegram Bot** (if configured).
    *   Launch the **Django Development Server**.

### Android (Termux)

To install on Termux, run this magic command:
```bash
curl -L https://raw.githubusercontent.com/Fil-m/eme/main/bootstrap_eme.sh | bash
```

---

## 🛠 Tech Stack

*   **Backend**: Django 5.1 + REST Framework
*   **Frontend**: Vue 3 (Reactive components) + Tabler UI
*   **AI Engine**: Ollama (local)
*   **Database**: SQLite (default)

---

## 🛡 License

MIT License. Designed and developed by Fil-m.
