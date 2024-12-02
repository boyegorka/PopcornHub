from import_export import resources
from .models import Movie, Cinema, Showtime

class MovieResource(resources.ModelResource):
     # Указываем, какие поля должны быть экспортированы
    class Meta:
        model = Movie
        fields = ('id', 'title', 'description', 'release_date', 'duration')  # Укажите все необходимые поля
        export_order = ('id', 'title', 'description', 'release_date', 'duration')  # Порядок полей при экспорте

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
        fields = ('id', 'name', 'address')  # Поля для экспорта
        export_order = ('id', 'name', 'address')  # Задаём порядок полей


# Ресурс для Showtime
class ShowtimeResource(resources.ModelResource):
    class Meta:
        model = Showtime
        fields = ('id', 'movie', 'cinema', 'start_time', 'ticket_price')  # Поля для экспорта
        export_order = ('id', 'movie', 'cinema', 'start_time', 'ticket_price')  # Задаём порядок