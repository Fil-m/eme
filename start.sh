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
    
    echo "🛠 Встановлюємо системні залежності (Media, XML, FFmpeg)..."
    pkg install python python-numpy curl unzip git libjpeg-turbo libpng ffmpeg libxml2 libxslt -y
    
    echo "🌐 Створюємо venv з доступом до системних пакетів (для швидкості)..."
    python -m venv venv --system-site-packages
    source venv/bin/activate
    
    echo "pip: Оновлюємо pip..."
    pip install --upgrade pip
    
    echo "pip: Встановлюємо Python залежності..."
    # Numpy вже встановлено системно, pip його пропустить або оновить швидко
    pip install -r requirements.txt
    
    echo "✅ Початкове налаштування завершено!"
else
    source venv/bin/activate
fi

echo "🗄 Перевірка та налаштування бази даних..."
python manage.py migrate
# python manage.py seed_nav # Вимкнено для запобігання втраті ручних змін

# 3. Налаштування SSL та запуск сервера
echo "🔐 Перевірка безпеки з'єднання..."
python setup_ssl.py

if [ -f "cert.pem" ] && [ -f "key.pem" ]; then
    echo "🟢 Захищений режим (HTTPS) активовано."
    LOCAL_IP=$(python -c 'import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8", 80)); print(s.getsockname()[0]); s.close()')
    echo "🔗 Доступ за адресою: https://$LOCAL_IP:8000"
    python manage.py runsslserver 0.0.0.0:8000 --certificate cert.pem --key key.pem
else
    echo "🔴 Помилка SSL: Сертифікати не знайдено."
    echo "Просимо встановити mkcert (choco install mkcert / pkg install mkcert) для роботи камери."
    echo "📱 Запуск у звичайному режимі (HTTP): http://$LOCAL_IP:8000"
    python manage.py runserver 0.0.0.0:8000
fi
