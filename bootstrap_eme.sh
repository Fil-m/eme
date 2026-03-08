# EME OS - GitHub Installer for Termux
# Цей скрипт автоматизує розгортання прямо з GitHub.

echo "📦 Початкове налаштування Termux..."
termux-setup-storage
pkg update -y && pkg upgrade -y

# 1. Встановлення базових інструментів для клонування
echo "💾 Встановлення Git..."
pkg install git -y

# 2. Клонування репозиторію
if [ ! -d "eme" ]; then
    echo "🌐 Клонування репозиторію з GitHub..."
    git clone https://github.com/Fil-m/eme.git
    cd eme
else
    echo "🔄 Оновлення коду..."
    cd eme
    git pull
fi

# 3. Перехід до основного процесу
echo "🚀 Запуск EME OS..."
bash start.sh
