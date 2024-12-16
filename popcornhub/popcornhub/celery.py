import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'popcornhub.settings')

# Create celery app
app = Celery('popcornhub')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'cleanup-old-ratings': {
        'task': 'showcase.tasks.cleanup_old_ratings',
        'schedule': crontab(hour=0, minute=0),  # Run daily at midnight
    },
    'update-movie-ratings': {
        'task': 'showcase.tasks.update_movie_ratings',
        'schedule': crontab(minute='*/30'),  # Run every 30 minutes
    },
} 