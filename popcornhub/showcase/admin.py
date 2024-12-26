from django.contrib import admin
from .models import Movie, Cinema, Showtime, Actor, Genre, Favorite, MovieRating, OnlineCinema, MovieOnlineCinema, UserVisit
from django.utils.safestring import mark_safe  # Для безопасного рендеринга HTML
from import_export.admin import ExportMixin, ExportActionModelAdmin
from import_export.formats import base_formats
from simple_history.admin import SimpleHistoryAdmin

from import_export import resources
from .resources import MovieResource, CinemaResource, ShowtimeResource, ActorResource, GenreResource, FavoriteResource, MovieRatingResource, OnlineCinemaResource, MovieOnlineCinemaResource

# Админка для модели Movie
@admin.register(Movie)
class MovieAdmin(ExportActionModelAdmin, ExportMixin, SimpleHistoryAdmin):
    formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]
    list_display = ('title', 'release_date', 'duration', 'poster_preview')  # Отображаем поле превью постера
    search_fields = ('title',)  # Поиск по названию фильма
    list_filter = ('release_date', 'genres__name')  # Фильтрация по дате релиза и жанру
    ordering = ('release_date',)  # Сортировка по дате выхода фильма
    resource_class = MovieResource

    # Функция для отображения изображения в списке
    def poster_preview(self, obj):
        if obj.poster:
            return mark_safe(f'<img src="{obj.poster.url}" style="width: 100px; height: auto;" />')  # Отображаем изображение
        return "No Image"  # Если изображения нет, показываем текст

    poster_preview.allow_tags = True  # Разрешаем вывод HTML для тега <img>
    poster_preview.short_description = 'Poster Preview'  # Название столбца в админке

# Админка для модели Cinema
@admin.register(Cinema)
class CinemaAdmin(ExportMixin, SimpleHistoryAdmin):
    list_display = ('name', 'address')  # Поля, которые будут отображаться в списке
    search_fields = ('name', 'address')  # Поиск по имени и адресу кинотеатра
    ordering = ('name',)  # Сортировка по имени кинотеатра
    resource_class = CinemaResource

# Админка для модели Showtime
@admin.register(Showtime)
class ShowtimeAdmin(ExportMixin, SimpleHistoryAdmin):
    list_display = ('movie', 'cinema', 'start_time', 'ticket_price')  # Поля для отображения
    list_filter = ('cinema', 'start_time')  # Фильтрация по кинотеатру и времени начала сеанса
    search_fields = ('movie__title', 'cinema__name')  # Поиск по названию фильма и кинотеатра
    ordering = ('start_time',)  # Сортировка по времени начала сеанса
    resource_class = ShowtimeResource

# Админка для модели Actor
@admin.register(Actor)
class ActorAdmin(ExportActionModelAdmin, ExportMixin, SimpleHistoryAdmin):
    formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]
    list_display = ('name', 'date_of_birth')  # Отображаем имя и дату рождения актёра
    search_fields = ('name',)  # Поиск по имени актёра
    ordering = ('name',)  # Сортировка по имени актёра
    resource_class = ActorResource

# Админка для модели Genre
@admin.register(Genre)
class GenreAdmin(ExportMixin, SimpleHistoryAdmin):
    list_display = ('name',)  # Отображаем только название жанра
    search_fields = ('name',)  # Поиск по названию жанра
    ordering = ('name',)  # Сортировка по названию жанра
    resource_class = GenreResource

# Админка для модели Favorite
@admin.register(Favorite)
class FavoriteAdmin(ExportMixin, SimpleHistoryAdmin):
    list_display = ('user', 'movie')  # Отображаем пользователя и фильм
    search_fields = ('user__username', 'movie__title')  # Поиск по имени пользователя и названию фильма
    ordering = ('user',)  # Сортировка по пользов��телю
    resource_class = FavoriteResource

# Админка для модели MovieRating
@admin.register(MovieRating)
class MovieRatingAdmin(ExportMixin, SimpleHistoryAdmin):
    list_display = ('movie', 'user', 'rating')  # Отображаем фильм, пользователя и рейтинг
    search_fields = ('movie__title', 'user__username')  # Поиск по названию фильма и имени пользователя
    list_filter = ('rating',)  # Фильтрация по рейтингу
    ordering = ('movie',)  # Сортировка по фильму
    resource_class = MovieRatingResource

# Админка для модели OnlineCinema
@admin.register(OnlineCinema)
class OnlineCinemaAdmin(ExportMixin, SimpleHistoryAdmin):
    list_display = ('name', 'url')  # Отображаем название и URL онлайн кинотеатра
    search_fields = ('name', 'url')  # Поиск по названию и URL
    ordering = ('name',)  # Сортировка по названию
    resource_class = OnlineCinemaResource

# Админка для модели MovieOnlineCinema
@admin.register(MovieOnlineCinema)
class MovieOnlineCinemaAdmin(ExportMixin, SimpleHistoryAdmin):
    list_display = ('movie', 'online_cinema')  # Отображаем фильм и онлайн кинотеатр
    search_fields = ('movie__title', 'online_cinema__name')  # Поиск по названию фильма и онлайн кинотеатра
    ordering = ('movie',)  # Сортировка по фильму
    resource_class = MovieOnlineCinemaResource

# Админка для модели UserVisit
@admin.register(UserVisit)
class UserVisitAdmin(ExportMixin, SimpleHistoryAdmin):
    list_display = ('user', 'path', 'method', 'ip_address', 'timestamp')
    list_filter = ('method', 'timestamp', 'user')
    search_fields = ('user__username', 'path', 'ip_address')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
