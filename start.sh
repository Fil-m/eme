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
    
    echo "🛠 Встановлюємо системні залежності та інструменти збірки..."
    # Додаємо rust, binutils, openssl та libffi, щоб pip зміг сам зібрати складні пакети на будь-якому телефоні
    pkg install python python-numpy curl unzip git libjpeg-turbo libpng ffmpeg libxml2 libxslt rust binutils openssl libffi -y
    
    # Виправляємо Android API level для компіляторів у Termux
    export ANDROID_API_LEVEL=24
    
    echo "🌐 Створюємо venv..."
    python -m venv venv --system-site-packages
    source venv/bin/activate
    
    echo "pip: Оновлюємо інструменти..."
    pip install --upgrade pip setuptools wheel
    
    echo "pip: Встановлюємо Python залежності..."
    pip install -r requirements.txt
    
    echo "✅ Початкове налаштування завершено!"
else
    source venv/bin/activate
    # На всякий випадок експортуємо змінні і при звичайному запуску
    export ANDROID_API_LEVEL=24
fi

echo "📦 Перевірка та оновлення залежностей..."
# Завжди перевіряємо залежності, щоб автоматично додати нові (sslserver, psutil)
pip install -r requirements.txt

echo "🗄 Налаштування структури бази даних..."
python manage.py migrate

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
