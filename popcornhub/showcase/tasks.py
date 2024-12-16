from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_movie_notification(movie_title, user_email):
    subject = f'New Movie Added: {movie_title}'
    message = f'A new movie "{movie_title}" has been added to our database!'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )

@shared_task
def update_movie_ratings():
    from .models import Movie, MovieRating
    from django.db.models import Avg
    
    for movie in Movie.objects.all():
        avg_rating = MovieRating.objects.filter(movie=movie).aggregate(Avg('rating'))['rating__avg']
        if avg_rating:
            # Здесь можно добавить логику обновления рейтинга
            print(f"Movie: {movie.title}, Average Rating: {avg_rating}") 