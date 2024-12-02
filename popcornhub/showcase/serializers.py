from rest_framework import serializers
from .models import Movie, Cinema, Showtime

# Сериализатор для модели Movie
class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ('id', 'title', 'description', 'release_date', 'duration', 'poster')

# Сериализатор для модели Cinema
class CinemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cinema
        fields = ('id', 'name', 'address')

# Сериализатор для модели Showtime
class ShowtimeSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()  # Вложенный сериализатор для фильма
    cinema = CinemaSerializer()  # Вложенный сериализатор для кинотеатра

    class Meta:
        model = Showtime
        fields = ('id', 'movie', 'cinema', 'start_time', 'ticket_price')
