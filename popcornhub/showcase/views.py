from .models import Movie, Cinema, Showtime
from .serializers import MovieSerializer, CinemaSerializer, ShowtimeSerializer
from rest_framework import viewsets
from .pagination import CustomPagination  # Импортируем кастомную пагинацию



# ViewSet для модели Movie
class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()  # Получаем все фильмы
    serializer_class = MovieSerializer  # Используем сериализатор для фильмов
    pagination_class = CustomPagination  # Применяем нашу кастомную пагинацию

# ViewSet для модели Cinema
class CinemaViewSet(viewsets.ModelViewSet):
    queryset = Cinema.objects.all()
    serializer_class = CinemaSerializer
    pagination_class = CustomPagination  # Применяем нашу кастомную пагинацию


# ViewSet для модели Showtime
class ShowtimeViewSet(viewsets.ModelViewSet):
    queryset = Showtime.objects.all()
    serializer_class = ShowtimeSerializer
    pagination_class = CustomPagination  # Применяем нашу кастомную пагинацию
