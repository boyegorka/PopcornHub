from import_export import resources
from import_export.formats import base_formats
from import_export.fields import Field
from django.db.models import Count
from django.utils import timezone

from .models import (
    Movie, Cinema, Showtime, Actor, Genre, Favorite, MovieRating,
    OnlineCinema, MovieOnlineCinema
)


# Ресурс для Movie
class MovieResource(resources.ModelResource):
    duration_formatted = Field()
    genres_list = Field()

    class Meta:
        model = Movie
        formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]  # Добавляем форматы
        fields = ('id', 'title', 'description', 'release_date', 'duration', 'duration_formatted', 'genres_list', 'average_rating')
        export_order = ('id', 'title', 'description', 'release_date', 'duration', 'duration_formatted', 'genres_list', 'average_rating')

    def get_export_queryset(self, *args, **kwargs):
        # Экспортируем только фильмы с рейтингом выше 5.0
        return Movie.objects.filter(average_rating__gte=5.0)

    def dehydrate_duration_formatted(self, obj):
        # Преобразуем длительность в часы и минуты
        hours = obj.duration // 60
        minutes = obj.duration % 60
        return f"{hours}ч {minutes}мин"

    def dehydrate_genres_list(self, obj):
        # Преобразуем жанры в строку, разделенную запятыми
        return ", ".join([genre.name for genre in obj.genres.all()])

    def dehydrate_release_date(self, obj):
        # Форматируем дату релиза
        return obj.release_date.strftime("%d %B %Y")


# Ресурс для Cinema
class CinemaResource(resources.ModelResource):
    movies_count = Field()
    full_address = Field()

    class Meta:
        model = Cinema
        formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]  # Добавляем форматы
        fields = ('id', 'name', 'address', 'full_address', 'movies_count')
        export_order = ('id', 'name', 'full_address', 'movies_count')

    def get_export_queryset(self, *args, **kwargs):
        # Экспортируем только кинотеатры с активными сеансами
        return Cinema.objects.annotate(
            showtime_count=Count('showtime')
        ).filter(showtime_count__gt=0)

    def dehydrate_movies_count(self, obj):
        # Подсчитываем количество уникальных фильмов в кинотеатре
        return Showtime.objects.filter(cinema=obj).values('movie').distinct().count()

    def dehydrate_full_address(self, obj):
        # Форматируем полный адрес
        return f"{obj.name}, {obj.address}"


# Ресурс для Showtime
class ShowtimeResource(resources.ModelResource):
    movie_duration = Field()
    formatted_price = Field()
    formatted_time = Field()

    class Meta:
        model = Showtime
        formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]  # Добавляем форматы
        fields = ('id', 'movie', 'cinema', 'start_time', 'formatted_time', 'ticket_price', 'formatted_price', 'movie_duration')
        export_order = ('id', 'movie', 'cinema', 'formatted_time', 'formatted_price', 'movie_duration')

    def get_export_queryset(self, *args, **kwargs):
        # Экспортируем только будущие сеансы
        return Showtime.objects.filter(start_time__gt=timezone.now())

    def dehydrate_movie_duration(self, obj):
        # Добавляем длительность фильма
        hours = obj.movie.duration // 60
        minutes = obj.movie.duration % 60
        return f"{hours}ч {minutes}мин"

    def dehydrate_formatted_price(self, obj):
        # Форматируем цену с валютой
        return f"${obj.ticket_price:.2f}"

    def dehydrate_formatted_time(self, obj):
        # Форматируем время начала сеанса
        return obj.start_time.strftime("%d.%m.%Y %H:%M")


# Ресурс для Actor
class ActorResource(resources.ModelResource):
    class Meta:
        model = Actor
        formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]  # Добавляем форматы
        fields = ('id', 'name', 'date_of_birth', 'biography')  # Поля для экспорта
        export_order = ('id', 'name', 'date_of_birth', 'biography')  # Задаём порядок полей


# Ресурс для Genre
class GenreResource(resources.ModelResource):
    class Meta:
        model = Genre
        formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]  # Добавляем форматы
        fields = ('id', 'name')  # Поля для экспорта
        export_order = ('id', 'name')  # Задаём порядок полей


# Ресурс для Favorite
class FavoriteResource(resources.ModelResource):
    class Meta:
        model = Favorite
        formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]  # Добавляем форматы
        fields = ('id', 'user', 'movie')  # Поля для экспорта
        export_order = ('id', 'user', 'movie')  # Задаём порядок полей


# Ресурс для MovieRating
class MovieRatingResource(resources.ModelResource):
    class Meta:
        model = MovieRating
        formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]  # Добавляем форматы
        fields = ('id', 'movie', 'user', 'rating')  # Поля для экспорта
        export_order = ('id', 'movie', 'user', 'rating')  # Задаём порядок полей


# Ресурс для OnlineCinema
class OnlineCinemaResource(resources.ModelResource):
    class Meta:
        model = OnlineCinema
        formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]  # Добавляем форматы
        fields = ('id', 'name', 'url')  # Поля для экспорта
        export_order = ('id', 'name', 'url')  # Задаём порядок полей


# Ресурс для MovieOnlineCinema
class MovieOnlineCinemaResource(resources.ModelResource):
    class Meta:
        model = MovieOnlineCinema
        formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]  # Добавляем форматы
        fields = ('id', 'movie', 'online_cinema')  # Поля для экспорта
        export_order = ('id', 'movie', 'online_cinema')  # Задаём порядок полей
