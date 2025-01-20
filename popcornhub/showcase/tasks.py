from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

import logging
import socket
from datetime import datetime

from django.db.models import (
    Avg, Count
)

from .models import (
    Movie, MovieRating
)

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_email_task(self):
    logger.info('=' * 50)
    logger.info('Starting email task')
    # Логируем настройки окружения
    logger.info(f'Task ID: {self.request.id}')
    logger.info(f'Current hostname: {socket.gethostname()}')
    # Логируем настройки email
    logger.info('Email settings:')
    logger.info(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
    logger.info(f'EMAIL_HOST: {settings.EMAIL_HOST}')
    logger.info(f'EMAIL_PORT: {settings.EMAIL_PORT}')
    logger.info(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
    logger.info(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
    try:
        # Проверяем доступность SMTP сервера
        logger.info(f'Attempting to connect to SMTP server: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
        smtp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        smtp.settimeout(5)
        result = smtp.connect_ex((settings.EMAIL_HOST, settings.EMAIL_PORT))
        if result == 0:
            logger.info('SMTP server is reachable')
        else:
            logger.error(f'SMTP server is not reachable, error code: {result}')
        smtp.close()
        # Отправляем письмо
        logger.info('Attempting to send email...')
        result = send_mail(
            subject='Test Subject',
            message='Test message body',
            from_email='noreply@popcornhub.com',
            recipient_list=['admin@example.com'],
            fail_silently=False,
        )
        logger.info(f'Email sent successfully with result: {result}')
        return f'Email sent successfully with result: {result}'
    except Exception as e:
        logger.error(f'Email sending failed: {str(e)}')
        self.retry(exc=e, countdown=5)


@shared_task
def periodic_task_demo():
    current_time = datetime.now().strftime('%H:%M:%S')
    message = '🕒 ПЕРИОДИЧЕСКАЯ ЗАДАЧА 🔔'
    logger.info('\n')
    logger.info('=' * 50)
    logger.info(message)
    logger.info(f'⏰ Время выполнения: {current_time}')
    logger.info('=' * 50)
    logger.info('\n')
    return message


@shared_task
def update_movie_statistics():
    current_time = datetime.now().strftime('%H:%M:%S')
    # Получаем все фильмы
    movies = Movie.objects.all()
    for movie in movies:
        # Подсчитываем статистику
        stats = MovieRating.objects.filter(movie=movie).aggregate(
            avg_rating=Avg('rating'),
            total_ratings=Count('rating')
        )
        # Обновляем информацию о фильме
        movie.average_rating = stats['avg_rating'] or 0.0
        movie.total_ratings = stats['total_ratings']
        movie.last_updated = datetime.now()
        movie.save()
        print(f'''
        {'=' * 50}
        📊 Обновлена статистика фильма:
        🎬 Название: {movie.title}
        ⭐ Средний рейтинг: {movie.average_rating:.2f}
        📈 Всего оценок: {movie.total_ratings}
        ⏰ Время обновления: {current_time}
        {'=' * 50}
        ''')
        return f'Статистика обновлена для {len(movies)} фильмов'


@shared_task
def update_movie_statuses():
    movies = Movie.objects.all()
    updated_count = 0
    
    for movie in movies:
        old_status = movie.status
        movie.update_status()
        if old_status != movie.status:
            updated_count += 1
            print(f'''
            {'=' * 50}
            🎬 Обновлен статус фильма:
            📽 Название: {movie.title}
            📅 Дата релиза: {movie.release_date}
            🔄 Старый статус: {old_status}
            ✨ Новый статус: {movie.status}
            {'=' * 50}
            ''')
    
    return f'Обновлены статусы для {updated_count} фильмов'
