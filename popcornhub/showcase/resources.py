from import_export import resources
from import_export.formats import base_formats
from .models import Movie, Cinema, Showtime, Actor, Genre, Favorite, MovieRating, OnlineCinema, MovieOnlineCinema

# Ресурс для Movie
class MovieResource(resources.ModelResource):
    class Meta:
        model = Movie
        formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]  # Добавляем форматы
        fields = ('id', 'title', 'description', 'release_date', 'duration', 'poster')  # Указываем все необходимые поля
        export_order = ('id', 'title', 'description', 'release_date', 'duration', 'poster')  # Порядок полей при экспорте

    # Метод для кастомизации данных при экспорте
    def dehydrate_title(self, movie):
        return movie.title.upper()  # Пример: делаем все заголовки заглавными

    def dehydrate_release_date(self, movie):
        # Преобразуем дату в более читаемый формат
        return movie.release_date.strftime('%d-%m-%Y')

    def get_export_queryset(self, request, *args, **kwargs):
        # Возвращаем только фильмы, которые были выпущены после 2000 года
        return Movie.objects.filter(release_date__year__gte=2000)


# Ресурс для Cinema
class CinemaResource(resources.ModelResource):
    class Meta:
        model = Cinema
        formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]  # Добавляем форматы

        fields = ('id', 'name', 'address')  # Поля для экспорта
        export_order = ('id', 'name', 'address')  # Задаём порядок полей


# Ресурс для Showtime
class ShowtimeResource(resources.ModelResource):
    class Meta:
        model = Showtime
        formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX]  # Добавляем форматы
        fields = ('id', 'movie', 'cinema', 'start_time', 'ticket_price')  # Поля для экспорта
        export_order = ('id', 'movie', 'cinema', 'start_time', 'ticket_price')  # Задаём порядок полей


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
