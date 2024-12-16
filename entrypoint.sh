#!/bin/sh

# Ждем, пока база данных станет доступной
echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.1
done
echo "PostgreSQL started"

# Ждем Redis
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
    sleep 0.1
done
echo "Redis started"

# Применяем миграции
python popcornhub/manage.py migrate --noinput

# Создаем суперпользователя
python popcornhub/manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print('Superuser created successfully')
    else:
        print('Superuser already exists')
except Exception as e:
    print(f'Error creating superuser: {str(e)}')
END

# Запускаем сервер с правильными настройками хоста
python popcornhub/manage.py runserver 0.0.0.0:8000