from rest_framework import serializers
from .models import Movie, Cinema, Showtime
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

# Сериализатор для модели Movie
class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ('id', 'title', 'description', 'release_date', 'duration', 'poster')

      # Дополнительное действие для получения фильмов, выпущенных после указанной даты
    @action(methods=['GET'], detail=False, url_path='released-after')
    def released_after(self, request):
        release_date = request.query_params.get('date')  # Получаем дату из параметров запроса
        if not release_date:
            return Response({"error": "date parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        movies = self.queryset.filter(release_date__gte=release_date)
        serializer = self.get_serializer(movies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Дополнительное действие для обновления описания конкретного фильма
    @action(methods=['POST'], detail=True, url_path='update-description')
    def update_description(self, request, pk=None):
        movie = self.get_object()
        new_description = request.data.get('description')
        if not new_description:
            return Response({"error": "description is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        movie.description = new_description
        movie.save()
        return Response({"message": "Description updated successfully"}, status=status.HTTP_200_OK)

# Сериализатор для модели Cinema
class CinemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cinema
        fields = ('id', 'name', 'address')

    # Получить список кинотеатров, содержащих слово в названии
    @action(methods=['GET'], detail=False, url_path='search-by-name')
    def search_by_name(self, request):
        name = request.query_params.get('name')
        if not name:
            return Response({"error": "name parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        cinemas = self.queryset.filter(name__icontains=name)
        serializer = self.get_serializer(cinemas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Сериализатор для модели Showtime
class ShowtimeSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()  # Вложенный сериализатор для фильма
    cinema = CinemaSerializer()  # Вложенный сериализатор для кинотеатра


    # Проверить, доступны ли билеты на сеанс
    @action(methods=['GET'], detail=True, url_path='check-tickets')
    def check_tickets(self, request, pk=None):
        showtime = self.get_object()
        # Например, проверяем наличие билетов через условие (моделируем)
        tickets_available = True  # Здесь можно реализовать логику проверки
        return Response({"showtime": showtime.id, "tickets_available": tickets_available})

    class Meta:
        model = Showtime
        fields = ('id', 'movie', 'cinema', 'start_time', 'ticket_price')
