#!/bin/bash

# EME OS - Termux Setup Script
# Цей скрипт автоматично налаштує оточення для запуску EME на вашому телефоні.

echo "🚀 Починаємо налаштування EME в Termux..."

# 1. Оновлення пакетів
echo "📦 Оновлюємо системні пакети..."
pkg update -y && pkg upgrade -y

# 2. Встановлення необхідних залежностей
echo "🛠 Встановлюємо Python, Git, Unzip та бібліотеки для Pillow..."
pkg install python git unzip libjpeg-turbo libpng -y

# 3. Налаштування віртуального середовища
echo "🌐 Налаштовуємо Python venv..."
python -m venv venv
source venv/bin/activate

# 4. Встановлення Python залежностей
echo "pip: Оновлюємо pip та встановлюємо залежності..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Міграції бази даних
echo "🗄 Налаштовуємо базу даних..."
python manage.py migrate
python manage.py seed_nav  # Заповнюємо початкові дані навігації

# 6. Створення скрипта для швидкого запуску
echo "📝 Створюємо скрипт запуску run_eme.sh..."
cat <<EOF > run_eme.sh
#!/bin/bash
source venv/bin/activate
echo "📱 EME OS запускається на http://127.0.0.1:8000"
echo "Для доступу з комп'ютера в тій же WiFi мережі використовуйте IP вашого телефону."
python manage.py runserver 0.0.0.0:8000
EOF
chmod +x run_eme.sh

echo ""
echo "✅ Налаштування завершено!"
echo "Запустіть проект командою: ./run_eme.sh"
