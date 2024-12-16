FROM python:3.11

WORKDIR /app

# Установка netcat для проверки доступности базы данных
RUN apt-get update && apt-get install -y netcat-traditional

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Исправляем права доступа для entrypoint.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Используем entrypoint.sh с полным путем
ENTRYPOINT ["/entrypoint.sh"]