from django.db import models
from simple_history.models import HistoricalRecords
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
import io
from django.urls import reverse



# Определяем менеджер до его использования
class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='published')


# Оригинальные модели
class Movie(models.Model):
    STATUS_CHOICES = [
        ('soon', 'Upcoming'),    # Еще не вышел
        ('now', 'Theaters'),  # Сейчас в кинотеатрах
        ('end', 'Ended')         # Прокат закончен
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    release_date = models.DateField()
    duration = models.PositiveIntegerField()  # в минутах
    poster = models.ImageField(upload_to='posters/', blank=True, null=True)
    trailer_video = models.FileField(
        upload_to='trailers/',
        null=True,
        blank=True,
        help_text='Upload movie trailer (MP4, MOV)',
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'mov'])]
    )
    genres = models.ManyToManyField('Genre', related_name='movies')
    average_rating = models.FloatField(default=0.0)
    total_ratings = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='soon'
    )
    history = HistoricalRecords()
    actors = models.ManyToManyField(
        'Actor',
        through='MovieActor',
        through_fields=('movie', 'actor'),
        related_name='acted_in_movies'
    )
    subtitle_file = models.FileField(
        upload_to='subtitles/',
        null=True,
        blank=True,
        help_text='Upload SRT or VTT subtitle file'
    )

    objects = models.Manager()
    published = PublishedManager()

    def calculate_status(self):
        today = timezone.now().date()
        release_date = self.release_date
        
        if release_date > today:
            return 'soon'
        elif (today - release_date).days <= 90:
            return 'now'
        else:
            return 'end'

    def save(self, *args, **kwargs):
        # Обработка статуса для новых и существующих записей
        new_status = self.calculate_status()
        if self.status != new_status:
            self.status = new_status

        # Обработка изображения при загрузке
        if self.poster and isinstance(self.poster, InMemoryUploadedFile):
            img = Image.open(self.poster)
            
            # Изменяем размер, сохраняя пропорции
            max_size = (800, 800)
            img.thumbnail(max_size, Image.LANCZOS)
            
            # Конвертируем в JPEG для уменьшения размера
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Сохраняем обработанное изображение
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            
            # Обновляем поле poster
            self.poster = InMemoryUploadedFile(
                output,
                'ImageField',
                f"{self.poster.name.split('.')[0]}.jpg",
                'image/jpeg',
                output.getbuffer().nbytes,
                None
            )

        super().save(*args, **kwargs)

    def update_status(self):
        today = timezone.now().date()
        days_difference = (today - self.release_date).days

        if days_difference < 0:  # Фильм еще не вышел
            new_status = 'soon'
        elif days_difference > 90:  # Прошло больше 90 дней
            new_status = 'end'
        else:  # Фильм в прокате
            new_status = 'now'

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])

    def get_absolute_url(self):
        return reverse('movie-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Movie'
        verbose_name_plural = 'Movies'
        ordering = ['-release_date']


class Cinema(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    # Пример валидации для уникальности адреса
    def clean(self):
        if Cinema.objects.filter(address=self.address).exists():
            raise ValidationError('Cinema with this address already exists.')

    class Meta:
        verbose_name = 'Cinema'
        verbose_name_plural = 'Cinemas'
        ordering = ['name']


class Showtime(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    ticket_price = models.DecimalField(max_digits=6, decimal_places=2)
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.movie.title} at {self.cinema.name} on {self.start_time}'

    # Пример валидации для времени начала сеанса
    def clean(self):
        if self.start_time < timezone.now():
            raise ValidationError('Showtime cannot be in the past.')


# Модель для актёров
class Actor(models.Model):
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    biography = models.TextField()
    movies = models.ManyToManyField('Movie', related_name='movie_actors', blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    # Пример валидации для возраста актера
    def clean(self):
        if self.date_of_birth > timezone.now().date():
            raise ValidationError('Date of birth cannot be in the future.')

    class Meta:
        verbose_name = 'Actor'
        verbose_name_plural = 'Actors'
        ordering = ['name']


# Модель для жанров
class Genre(models.Model):
    name = models.CharField(max_length=255)
    history = HistoricalRecords()

    def __str__(self):
        return self.name


# Модель для избранных фильмов
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_favorites')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='movie_favorites')
    
    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"


# Модель для рейтингов фильмов
class MovieRating(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=1, 
                               validators=[MinValueValidator(1), MaxValueValidator(10)])

    class Meta:
        unique_together = ['movie', 'user']
        verbose_name = 'Movie Rating'
        verbose_name_plural = 'Movie Ratings'

    def __str__(self):
        return f"{self.movie.title} - {self.user.username} - {self.rating}"


# Модель для онлайн кинотеатров
class OnlineCinema(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=255)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

    # Пример валидации для URL
    def clean(self):
        if not self.url.startswith('http'):
            raise ValidationError("URL must start with 'http'.")


# Модель для связи фильмов с онлайн кинотеатрами
class MovieOnlineCinema(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    online_cinema = models.ForeignKey(OnlineCinema, on_delete=models.CASCADE)
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.movie.title} on {self.online_cinema.name}'


class UserVisit(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
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
        return f'{self.user or "Anonymous"} - {self.path} at {self.timestamp}'


class MovieActor(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    is_main_role = models.BooleanField(default=False)

    class Meta:
        unique_together = ['movie', 'actor']
