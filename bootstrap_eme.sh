# EME OS - GitHub Installer for Termux
# Цей скрипт автоматизує розгортання прямо з GitHub.

echo "📦 Налаштування Termux..."
termux-setup-storage
pkg update -y && pkg upgrade -y

echo "🌐 Клонування EME OS з GitHub..."

# 1. Встановлення системних пакетів
pkg install git python openssl -y

# 2. Клонування
if [ ! -d "eme" ]; then
    git clone https://github.com/Fil-m/eme.git
    cd eme
else
    cd eme
    git pull
fi

# 3. Запуск основного скрипта
echo "🚀 Запуск конфігурації..."
bash start.sh
