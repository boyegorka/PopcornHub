from rest_framework import serializers

from .models import (
    Movie, Cinema, Showtime, Actor, Genre, Favorite, MovieRating,
    OnlineCinema, MovieOnlineCinema
)


# Сериализатор для модели Cinema
class CinemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cinema
        fields = ('id', 'name', 'address')

# Сериализатор для модели Actor
class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ('id', 'name', 'date_of_birth', 'biography')

# Сериализатор для модели Movie
class MovieSerializer(serializers.ModelSerializer):
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ('id', 'title', 'description', 'release_date', 'duration', 'poster', 'genres', 'actors')

# Сериализатор для модели Showtime
class ShowtimeSerializer(serializers.ModelSerializer):
    movie = MovieSerializer()  # Вложенный сериализатор для фильма
    cinema = CinemaSerializer()  # Вложенный сериализатор для кинотеатра

    class Meta:
        model = Showtime
        fields = ('id', 'movie', 'cinema', 'start_time', 'ticket_price')

# Сериализатор для модели Genre
class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'name')


# Сериализатор для модели Favorite
class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'user', 'movie')


# Сериализатор для модели MovieRating
class MovieRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieRating
        fields = ('id', 'movie', 'user', 'rating')


# Сериализатор для модели OnlineCinema
class OnlineCinemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineCinema
        fields = ('id', 'name', 'url')


# Сериализатор для модели MovieOnlineCinema
class MovieOnlineCinemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieOnlineCinema
        fields = ('id', 'movie', 'online_cinema')
