#!/bin/bash

# EME OS - Unified Start Script
# Цей скрипт автоматично налаштовує оточення (якщо треба) та запускає сервер.

echo "🚀 Запуск EME OS..."

# 1. Створення папок для медіа та логів
mkdir -p media
mkdir -p eme_media/previews
chmod -R 777 media
chmod -R 777 eme_media/previews

# 2. Перевірка віртуального середовища
if [ ! -d "venv" ]; then
    echo "⚠️ Віртуальне середовище не знайдено. Починаємо початкове налаштування..."
    
    echo "📦 Оновлюємо системні пакети..."
    pkg update -y && pkg upgrade -y
    
    echo "🛠 Встановлюємо залежності (Python, Unzip, Pillow libs)..."
    pkg install python unzip libjpeg-turbo libpng -y
    
    echo "🌐 Створюємо venv..."
    python -m venv venv
    source venv/bin/activate
    
    echo "pip: Встановлюємо Python залежності..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo "🗄 Налаштовуємо базу даних..."
    python manage.py migrate
    python manage.py seed_nav
    
    echo "✅ Налаштування завершено!"
else
    source venv/bin/activate
fi

# 3. Запуск сервера
echo "📱 EME OS запускається на http://127.0.0.1:8000"
echo "Для завершення натисніть Ctrl+C"
python manage.py runserver 0.0.0.0:8000
