from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from .models import (
    Movie, Cinema, Showtime, Actor, Genre, Favorite, MovieRating,
    OnlineCinema, MovieOnlineCinema
)
from .templatetags.movie_filters import duration_format, rating_stars


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

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Valid movie example',
            value={
                'title': 'The Matrix',
                'description': 'A computer programmer discovers a mysterious world...',
                'release_date': '1999-03-31',
                'duration': 136,
                'status': 'now'
            },
            request_only=True,
        )
    ]
)
class MovieSerializer(serializers.ModelSerializer):
    actors = ActorSerializer(many=True, read_only=True)
    formatted_duration = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_formatted = serializers.SerializerMethodField()
    title_short = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = (
            'id', 'title', 'title_short', 'description', 
            'release_date', 'duration', 'duration_formatted',
            'poster', 'genres', 'status', 'status_display',
            'average_rating', 'total_ratings', 'actors'
        )

    def get_formatted_duration(self, obj):
        return duration_format(obj.duration)

    def get_duration_formatted(self, obj):
        """Форматирует длительность фильма в часы и минуты"""
        hours = obj.duration // 60
        minutes = obj.duration % 60
        return f'{hours}ч {minutes:02d}мин'

    def get_title_short(self, obj):
        """Возвращает сокращенное название фильма"""
        if len(obj.title) > 30:
            return f'{obj.title[:30]}...'
        return obj.title

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
