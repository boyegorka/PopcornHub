from __future__ import (
    absolute_import,
    unicode_literals
)

import os
from datetime import timedelta

from celery import Celery


# Установите настройки Django для Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'popcornhub.settings')

# Создайте экземпляр приложения Celery
app = Celery('popcornhub')

app.conf.update(
    broker_url='redis://redis:6379/0',
    result_backend='redis://redis:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1
)

# Используйте настройки Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически найдите задачи в приложениях
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


app.conf.beat_schedule = {
    'demo-task-every-5-seconds': {
        'task': 'showcase.tasks.periodic_task_demo',
        'schedule': timedelta(seconds=5),
    },
    'send-email-every-minute': {
        'task': 'showcase.tasks.send_email_task',
        'schedule': timedelta(seconds=60),
    },
    'update-movie-stats-every-minute': {
        'task': 'showcase.tasks.update_movie_statistics',
        'schedule': timedelta(minutes=1),
    },
}
