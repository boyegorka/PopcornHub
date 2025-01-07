from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from datetime import timedelta
import random

from showcase.models import (
    Movie, Cinema, Showtime, Actor, Genre, Favorite, MovieRating,
    OnlineCinema, MovieOnlineCinema
)


class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **kwargs):
        # Создаем жанры
        genres = [
            Genre.objects.create(name=name) for name in [
                'Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi',
                'Adventure', 'Romance', 'Thriller', 'Fantasy', 'Animation'
            ]
        ]
        # Создаем актеров
        actors = [
            Actor.objects.create(
                name=name,
                date_of_birth=timezone.now().date() - timedelta(days=365 * random.randint(20, 60)),
                biography=f'Biography of {name}'
            ) for name in [
                'Tom Cruise', 'Brad Pitt', 'Leonardo DiCaprio', 'Morgan Freeman',
                'Robert Downey Jr.', 'Jennifer Lawrence', 'Scarlett Johansson',
                'Emma Stone', 'Anne Hathaway', 'Meryl Streep'
            ]
        ]
        # Создаем фильмы
        movies = [
            Movie.objects.create(
                title=title,
                release_date=timezone.now().date() - timedelta(days=random.randint(0, 3650)),
                duration=random.randint(90, 180),
                description=f'Description of {title}',
                average_rating=round(random.uniform(1, 10), 1)
            ) for title in [
                'The Matrix', 'Inception', 'Interstellar', 'The Dark Knight',
                'Pulp Fiction', 'Fight Club', 'Forrest Gump', 'The Godfather',
                'Gladiator', 'Avatar'
            ]
        ]
        # Добавляем жанры к фильмам
        for movie in movies:
            movie.genres.add(*random.sample(genres, k=random.randint(1, 3)))
        # Создаем кинотеатры
        cinemas = [
            Cinema.objects.create(
                name=name,
                address=f'{random.randint(1, 100)} Main St, City'
            ) for name in [
                'AMC', 'Regal', 'Cinemark', 'IMAX Theater',
                'Landmark', 'Alamo Drafthouse', 'Century', 'United Artists',
                'Marcus Theatres', 'Showcase Cinema'
            ]
        ]
        # Создаем онлайн-кинотеатры
        online_cinemas = [
            OnlineCinema.objects.create(
                name=name,
                url=f'https://{name.lower().replace(" ", "")}.com'
            ) for name in [
                'Netflix', 'Amazon Prime', 'Disney Plus', 'HBO Max',
                'Hulu', 'Apple TV Plus', 'Peacock', 'Paramount Plus',
                'Crunchyroll', 'Mubi'
            ]
        ]
        # Создаем сеансы
        for _ in range(10):
            Showtime.objects.create(
                movie=random.choice(movies),
                cinema=random.choice(cinemas),
                start_time=timezone.now() + timedelta(days=random.randint(1, 30)),
                ticket_price=round(random.uniform(8, 20), 2)
            )
        # Создаем тестового пользователя
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'is_staff': True
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        # Создаем избранные фильмы
        for movie in random.sample(movies, k=5):
            Favorite.objects.create(
                user=user,
                movie=movie
            )
        # Создаем оценки фильмов
        for movie in movies:
            MovieRating.objects.create(
                movie=movie,
                user=user,
                rating=random.randint(1, 10)
            )
        # Создаем связи фильмов с онлайн-кинотеатрами
        for movie in movies:
            for online_cinema in random.sample(online_cinemas, k=random.randint(1, 3)):
                MovieOnlineCinema.objects.create(
                    movie=movie,
                    online_cinema=online_cinema
                )
        self.stdout.write(self.style.SUCCESS('Successfully populated database'))
