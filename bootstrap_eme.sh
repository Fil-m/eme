#!/bin/bash

# EME OS - Bootstrap Script for Termux
# Цей скрипт автоматизує все: скачування, розпакування та запуск.

# Користувач має вказати IP комп'ютера як аргумент
IP=$1

if [ -z "$IP" ]; then
    echo "❌ Помилка: Вкажіть IP вашого комп'ютера."
    echo "Приклад: bash bootstrap_eme.sh 192.168.1.10"
    exit 1
fi

echo "📡 Спроба завантажити проект з http://$IP:8080..."

# 1. Створення папки
mkdir -p eme_os
cd eme_os

# 2. Встановлення unzip та curl
echo "📦 Встановлення системних утиліт..."
pkg install unzip curl -y

# 3. Завантаження архіву
# Припускаємо, що на Windows запущено: python -m http.server 8080
curl -L "http://$IP:8080/eme_mobile_dist.zip" -o project.zip

if [ $? -ne 0 ]; then
    echo "❌ Помилка завантаження! Перевірте: "
    echo "1. Чи запущено на комп'ютері: python -m http.server 8080"
    echo "2. Чи вірний IP: $IP"
    echo "3. Чи обидва пристрої в одній WiFi мережі."
    exit 1
fi

# 4. Розпакування
echo "🔓 Розпакування..."
unzip -o project.zip
rm project.zip

# 5. Запуск основного скрипта
echo "🚀 Передаю керування start.sh..."
bash start.sh
