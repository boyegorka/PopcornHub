from django.db import models
from simple_history.models import HistoricalRecords
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model

# Оригинальные модели
class Movie(models.Model):
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    duration = models.IntegerField()  # Длительность в минутах
    description = models.TextField()
    poster = models.ImageField(upload_to='posters/', blank=True, null=True)
    genres = models.ManyToManyField('Genre', related_name='movies')  # Связь с жанрами
    history = HistoricalRecords()  # Исторические записи изменений
    average_rating = models.FloatField(default=0.0)

    def __str__(self):
        return self.title

    # Пример валидации для даты релиза фильма
    def clean(self):
        if self.release_date > timezone.now().date():
            raise ValidationError("Release date cannot be in the future.")


class Cinema(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    # Пример валидации для уникальности адреса
    def clean(self):
        if Cinema.objects.filter(address=self.address).exists():
            raise ValidationError("Cinema with this address already exists.")


class Showtime(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    ticket_price = models.DecimalField(max_digits=6, decimal_places=2)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.movie.title} at {self.cinema.name} on {self.start_time}"

    # Пример валидации для времени начала сеанса
    def clean(self):
        if self.start_time < timezone.now():
            raise ValidationError("Showtime cannot be in the past.")


# Модель для актёров
class Actor(models.Model):
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    biography = models.TextField()
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    # Пример валидации для возраста актера
    def clean(self):
        if self.date_of_birth > timezone.now().date():
            raise ValidationError("Date of birth cannot be in the future.")


# Модель для жанров
class Genre(models.Model):
    name = models.CharField(max_length=255)
    history = HistoricalRecords()

    def __str__(self):
        return self.name


# Модель для избранных фильмов
class Favorite(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)  # Подключаем к пользователю
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('user', 'movie')  # Каждый фильм может быть в избранном только у одного пользователя

    def __str__(self):
        return f"{self.user.username}'s favorite movie: {self.movie.title}"


# Модель для оценок фильмов
class MovieRating(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  # Оценка от 1 до 10
    history = HistoricalRecords()

    class Meta:
        unique_together = ('movie', 'user')

    def __str__(self):
        return f"Rating for {self.movie.title} by {self.user.username}: {self.rating}"


# Модель для онлайн кинотеатров
class OnlineCinema(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=255)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    # Пример валидации для URL
    def clean(self):
        if not self.url.startswith("http"):
            raise ValidationError("URL must start with 'http'.")


# Модель для связи фильмов с онлайн кинотеатрами
class MovieOnlineCinema(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    online_cinema = models.ForeignKey(OnlineCinema, on_delete=models.CASCADE)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.movie.title} on {self.online_cinema.name}"


class UserVisit(models.Model):
    user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Visit'
        verbose_name_plural = 'User Visits'
        app_label = 'auth'  # Это переместит модель в секцию Authentication and Authorization

    def __str__(self):
        return f"{self.user or 'Anonymous'} - {self.path} at {self.timestamp}"
