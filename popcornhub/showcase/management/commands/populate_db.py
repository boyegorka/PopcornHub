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
        try:
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
            # Создаем фильмы с разными датами релиза для разных статусов
            today = timezone.now().date()
            
            # Upcoming movies (будущая дата)
            upcoming_movies = [
                Movie.objects.create(
                    title=f"Upcoming Movie {i}",
                    release_date=today + timedelta(days=random.randint(1, 365)),
                    duration=random.randint(90, 180),
                    description=f"Description of upcoming movie {i}",
                    average_rating=0.0
                ) for i in range(3)
            ]
            
            # In theaters movies (в пределах 30 дней от сегодня)
            in_theaters_movies = [
                Movie.objects.create(
                    title=f"In Theaters Movie {i}",
                    release_date=today - timedelta(days=random.randint(0, 29)),
                    duration=random.randint(90, 180),
                    description=f"Description of movie in theaters {i}",
                    average_rating=round(random.uniform(1, 10), 1)
                ) for i in range(4)
            ]
            
            # Ended movies (старше 30 дней)
            ended_movies = [
                Movie.objects.create(
                    title=f"Ended Movie {i}",
                    release_date=today - timedelta(days=random.randint(31, 365)),
                    duration=random.randint(90, 180),
                    description=f"Description of ended movie {i}",
                    average_rating=round(random.uniform(1, 10), 1)
                ) for i in range(3)
            ]
            
            movies = upcoming_movies + in_theaters_movies + ended_movies
            
            # Добавляем жанры к фильмам
            for movie in movies:
                movie.genres.add(*random.sample(genres, k=random.randint(1, 3)))
            # Добавляем актёров к фильмам
            for movie in movies:
                # Случайно выбираем от 2 до 5 актёров для каждого фильма
                movie_actors = random.sample(actors, k=random.randint(2, 5))
                movie.actors.add(*movie_actors)
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
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error populating database: {str(e)}'))
