from django.db import models
from simple_history.models import HistoricalRecords
from django.core.exceptions import ValidationError
from django.utils import timezone

# Модель для фильмов
class Movie(models.Model):
    title = models.CharField(max_length=200)  # Название фильма
    description = models.TextField()  # Описание
    release_date = models.DateField()  # Дата выхода
    duration = models.PositiveIntegerField()  # Длительность в минутах
    poster = models.ImageField(upload_to="posters/", blank=True, null=True)  # Постер
    history = HistoricalRecords()  # Подключаем историю

    # Валидация
    def clean(self):
        # Проверка, что дата выпуска фильма не позже текущей даты
        if self.release_date > timezone.now().date():
            raise ValidationError("Release date cannot be in the future.")

        # Валидация длительности фильма (должна быть положительная)
        if self.duration <= 0:
            raise ValidationError("Duration must be a positive value.")

        # Проверка уникальности названия фильма для пользователя
        if Movie.objects.filter(title=self.title, user=self.user).exists():
            raise ValidationError("A movie with this title already exists for the user.")
        
        super().clean()

    def __str__(self):
        return self.title

# Модель для кинотеатров
class Cinema(models.Model):
    name = models.CharField(max_length=150)  # Название кинотеатра
    address = models.CharField(max_length=300)  # Адрес
    history = HistoricalRecords()  # Подключаем историю

    # Модель кинотеатра
    class Cinema(models.Model):
        name = models.CharField(max_length=255)
        address = models.CharField(max_length=255)
        user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

        # Валидация
        def clean(self):
            # Проверка, что адрес кинотеатра имеет правильный формат
            if not self.address:
                raise ValidationError("Address cannot be empty.")
            
            # Проверка уникальности названия кинотеатра для пользователя
            if Cinema.objects.filter(name=self.name, user=self.user).exists():
                raise ValidationError("A cinema with this name already exists for the user.")
            
            super().clean()

    def __str__(self):
        return self.name

# Модель для сеансов
class Showtime(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="showtimes")  # Фильм
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE, related_name="showtimes")  # Кинотеатр
    start_time = models.DateTimeField()  # Дата и время начала сеанса
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена билета
    history = HistoricalRecords()  # Подключаем историю

    # Модель сеанса
    class Showtime(models.Model):
        movie = models.ForeignKey('Movie', on_delete=models.CASCADE)
        cinema = models.ForeignKey('Cinema', on_delete=models.CASCADE)
        start_time = models.DateTimeField()
        end_time = models.DateTimeField()
        ticket_price = models.DecimalField(max_digits=8, decimal_places=2)

        # Валидация
        def clean(self):
            # Проверка, что время начала не позже времени окончания
            if self.start_time > self.end_time:
                raise ValidationError("Start time cannot be later than end time.")

            # Проверка наличия фильма и кинотеатра
            if not self.movie or not self.cinema:
                raise ValidationError("Both movie and cinema must be specified.")

            super().clean()

    def __str__(self):
        return f"{self.movie.title} at {self.cinema.name} on {self.start_time}"