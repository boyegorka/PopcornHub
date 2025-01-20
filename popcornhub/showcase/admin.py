from django.contrib import admin
from django.utils.safestring import mark_safe  # Для безопасного рендеринга HTML
from import_export.admin import (ExportActionModelAdmin, ExportMixin)
from import_export.formats import base_formats
from simple_history.admin import SimpleHistoryAdmin
from django.http import HttpResponse
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.contrib import messages

from .resources import (
    MovieResource, CinemaResource, ShowtimeResource, ActorResource,
    GenreResource, FavoriteResource, MovieRatingResource,
    OnlineCinemaResource, MovieOnlineCinemaResource
)
from .models import (
    Movie, Cinema, Showtime, Actor, Genre, Favorite, MovieRating,
    OnlineCinema, MovieOnlineCinema, UserVisit, MovieActor
)


# Определяем все inline-классы в начале файла
class MovieActorInline(admin.TabularInline):
    model = MovieActor
    extra = 1
    fields = ['actor', 'role', 'is_main_role']

class MovieRatingInline(admin.TabularInline):
    model = MovieRating
    extra = 1
    fields = ['user', 'rating']
    readonly_fields = ['user']

class ShowtimeInline(admin.TabularInline):
    model = Showtime
    extra = 1
    fields = ['movie', 'start_time', 'ticket_price']


# Админка для модели Movie
@admin.register(Movie)
class MovieAdmin(ExportActionModelAdmin, ExportMixin, SimpleHistoryAdmin):
    formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]
    list_display = (
        'title', 
        'release_date', 
        'duration', 
        'poster_preview', 
        'average_rating',
        'get_status_display_colored',  # Добавляем статус
        'total_ratings',  # Добавляем количество оценок
        'has_trailer'  # Добавляем флаг наличия трейлера
    )
    search_fields = ('title', 'description')  # Поиск по названию и описанию фильма
    list_filter = ('release_date', 'genres__name', 'status')  # Фильтрация по дате релиза, жанру и статусу
    ordering = ('release_date',)  # Сортировка по дате выхода фильма
    resource_class = MovieResource
    readonly_fields = ('status', 'average_rating', 'total_ratings', 'last_updated')  # Делаем поля только для чтения
    inlines = [MovieActorInline, MovieRatingInline]

    def get_status_display_colored(self, obj):
        """Отображение статуса с цветовой индикацией"""
        colors = {
            'upcoming': 'blue',
            'in_theaters': 'green',
            'ended': 'red'
        }
        color = colors.get(obj.status, 'black')
        status_display = obj.get_status_display()
        return mark_safe(f'<span style="color: {color}; font-weight: bold;">{status_display}</span>')
    
    get_status_display_colored.short_description = 'Status'  # Название столбца
    get_status_display_colored.admin_order_field = 'status'  # Возможность сортировки

    # Функция для отображения изображения в списке
    def poster_preview(self, obj):
        if obj.poster:
            return mark_safe(f'<img src="{obj.poster.url}" style="width: 100px; height: auto;" />')  # Отображаем изображение
        return 'No Image'  # Если изображения нет, показываем текст

    poster_preview.allow_tags = True  # Разрешаем вывод HTML для тега <img>
    poster_preview.short_description = 'Poster Preview'  # Название столбца в админке

    # Добавляем дополнительную информацию в детальном просмотре
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'release_date', 'duration', 'poster')
        }),
        ('Media', {
            'fields': ('trailer_video',),
            'classes': ('collapse',)
        }),
        ('Categories', {
            'fields': ('genres',)
        }),
        ('Statistics', {
            'fields': ('status', 'average_rating', 'total_ratings'),
            'classes': ('collapse',)
        })
    )

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    # Добавляем действие для ручного обновления статуса
    actions = ['update_movie_statuses', 'export_as_pdf']

    def update_movie_statuses(self, request, queryset):
        updated = 0
        for movie in queryset:
            old_status = movie.status
            movie.update_status()
            if old_status != movie.status:
                updated += 1
        
        if updated:
            self.message_user(request, f'Successfully updated {updated} movie statuses.')
        else:
            self.message_user(request, 'No status changes were needed.')
    
    update_movie_statuses.short_description = "Update selected movies' statuses"

    def export_as_pdf(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="movies.pdf"'
        
        # Create PDF
        p = canvas.Canvas(response, pagesize=letter)
        y = 750  # Starting y position
        
        for movie in queryset:
            p.drawString(100, y, f"Title: {movie.title}")
            p.drawString(100, y-20, f"Release Date: {movie.release_date}")
            p.drawString(100, y-40, f"Duration: {movie.duration} minutes")
            p.drawString(100, y-60, f"Status: {movie.get_status_display()}")
            y -= 100  # Move down for next movie
            
            if y <= 50:  # New page if running out of space
                p.showPage()
                y = 750
        
        p.showPage()
        p.save()
        return response
    
    export_as_pdf.short_description = "Export selected movies to PDF"

    def has_trailer(self, obj):
        return bool(obj.trailer_video)
    has_trailer.boolean = True
    has_trailer.short_description = 'Has Trailer'

    def save_model(self, request, obj, form, change):
        if obj.trailer_video:
            # Проверяем размер файла (не более 100MB)
            if obj.trailer_video.size > 100 * 1024 * 1024:
                messages.error(request, 'Trailer file is too large. Maximum size is 100MB.')
                return
        super().save_model(request, obj, form, change)


# Админка для модели Cinema
@admin.register(Cinema)
class CinemaAdmin(ExportMixin, SimpleHistoryAdmin):
    list_display = ('name', 'address')  # Поля, которые будут отображаться в списке
    search_fields = ('name', 'address')  # Поиск по имени и адресу кинотеатра
    ordering = ('name',)  # Сортировка по имени кинотеатра
    resource_class = CinemaResource
    inlines = [ShowtimeInline]


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
    ordering = ('user',)  # Сортировка по пользователю
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

    def get_app_label(self):
        return 'auth'  # Перемещаем в раздел Authentication and Authorization
