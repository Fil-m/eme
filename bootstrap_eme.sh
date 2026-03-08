# EME OS - GitHub Installer for Termux
# Цей скрипт автоматизує розгортання прямо з GitHub.

echo "🌐 Клонування EME OS з GitHub..."

# 1. Встановлення git
pkg install git python -y

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
