from django.contrib import admin
from .models import Movie, Cinema, Showtime
from django.utils.safestring import mark_safe  # Для безопасного рендеринга HTML
from import_export.admin import ExportMixin
from simple_history.admin import SimpleHistoryAdmin

from import_export import resources
from .resources import MovieResource, CinemaResource, ShowtimeResource

# Админка для модели Movie
@admin.register(Movie)
class MovieAdmin(ExportMixin, SimpleHistoryAdmin):
    list_display = ('title', 'release_date', 'duration', 'poster_preview')  # Отображаем поле превью постера
    search_fields = ('title',)  # Поиск по названию фильма
    list_filter = ('release_date',)  # Фильтрация по дате релиза
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
