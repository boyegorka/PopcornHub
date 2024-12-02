from django.db import models
from simple_history.models import HistoricalRecords

# Модель для фильмов
class Movie(models.Model):
    title = models.CharField(max_length=200)  # Название фильма
    description = models.TextField()  # Описание
    release_date = models.DateField()  # Дата выхода
    duration = models.PositiveIntegerField()  # Длительность в минутах
    poster = models.ImageField(upload_to="posters/", blank=True, null=True)  # Постер
    history = HistoricalRecords()  # Подключаем историю

    def __str__(self):
        return self.title

# Модель для кинотеатров
class Cinema(models.Model):
    name = models.CharField(max_length=150)  # Название кинотеатра
    address = models.CharField(max_length=300)  # Адрес
    history = HistoricalRecords()  # Подключаем историю

    def __str__(self):
        return self.name

# Модель для сеансов
class Showtime(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="showtimes")  # Фильм
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE, related_name="showtimes")  # Кинотеатр
    start_time = models.DateTimeField()  # Дата и время начала сеанса
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена билета
    history = HistoricalRecords()  # Подключаем историю

    def __str__(self):
        return f"{self.movie.title} at {self.cinema.name} on {self.start_time}"