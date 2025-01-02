from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging
import socket
from datetime import datetime

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def send_email_task(self):
    logger.info("="*50)
    logger.info("Starting email task")
    
    # Логируем настройки окружения
    logger.info(f"Task ID: {self.request.id}")
    logger.info(f"Current hostname: {socket.gethostname()}")
    
    # Логируем настройки email
    logger.info("Email settings:")
    logger.info(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    logger.info(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    logger.info(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    logger.info(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    logger.info(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    try:
        # Проверяем доступность SMTP сервера
        logger.info(f"Attempting to connect to SMTP server: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        smtp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        smtp.settimeout(5)
        result = smtp.connect_ex((settings.EMAIL_HOST, settings.EMAIL_PORT))
        if result == 0:
            logger.info("SMTP server is reachable")
        else:
            logger.error(f"SMTP server is not reachable, error code: {result}")
        smtp.close()

        # Отправляем письмо
        logger.info("Attempting to send email...")
        result = send_mail(
            subject='Test Subject',
            message='Test message body',
            from_email='noreply@popcornhub.com',
            recipient_list=['admin@example.com'],
            fail_silently=False,
        )
        
        logger.info(f"Email sent successfully with result: {result}")
        return f"Email sent successfully with result: {result}"
    
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        self.retry(exc=e, countdown=5)

@shared_task
def test_redis():
    logger.info("Testing Redis connection")
    try:
        # Проверяем подключение к Redis
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        redis_conn.ping()
        logger.info("Redis connection successful!")
        return "Redis connection successful!"
    except Exception as e:
        logger.error(f"Redis connection failed: {str(e)}")
        raise

@shared_task
def test_connections():
    logger.info("="*50)
    logger.info("Starting connection tests")
    
    # 1. Проверка Redis
    try:
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        redis_conn.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {str(e)}")

    # 2. Проверка PostgreSQL
    try:
        from django.db import connections
        conn = connections['default']
        conn.cursor()
        logger.info("✅ PostgreSQL connection successful")
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {str(e)}")

    # 3. Проверка Mailhog
    try:
        import socket
        smtp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        smtp.settimeout(5)
        result = smtp.connect_ex((settings.EMAIL_HOST, settings.EMAIL_PORT))
        if result == 0:
            logger.info("✅ Mailhog SMTP connection successful")
        else:
            logger.error(f"❌ Mailhog SMTP connection failed with code: {result}")
        smtp.close()
    except Exception as e:
        logger.error(f"❌ Mailhog connection test failed: {str(e)}")

    # 4. Проверка DNS резолвинга
    for host in ['redis', 'db', 'mailhog']:
        try:
            ip = socket.gethostbyname(host)
            logger.info(f"✅ DNS resolution for {host}: {ip}")
        except Exception as e:
            logger.error(f"❌ DNS resolution failed for {host}: {str(e)}")

    logger.info("="*50)

@shared_task
def periodic_task_demo():
    current_time = datetime.now().strftime("%H:%M:%S")
    message = f"🕒 ПЕРИОДИЧЕСКАЯ ЗАДАЧА 🔔"
    logger.info("\n")
    logger.info("="*50)
    logger.info(message)
    logger.info(f"⏰ Время выполнения: {current_time}")
    logger.info("="*50)
    logger.info("\n")
    return message
