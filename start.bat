@echo off
echo Starting Ollama...
start "Ollama Server" ollama serve

echo Starting EME Telegram Bot...
start "EME Telegram Bot" cmd /c "cd /d d:\dev\eme-telegram-bot && call venv\Scripts\activate.bat && python -m bot"

echo Starting EME OS Server...
set PYTHONUTF8=1
python manage.py runserver 0.0.0.0:8000
