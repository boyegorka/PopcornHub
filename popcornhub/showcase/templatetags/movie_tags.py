from django import template
from django.db.models import Count, Avg
from ..models import Movie, Genre, OnlineCinema
from django.utils import timezone
from django.db import connection
from django.db import reset_queries
import logging

logger = logging.getLogger(__name__)

register = template.Library()

@register.inclusion_tag('showcase/widgets/featured_movies.html')
def show_featured_movies():
    """Виджет для отображения топовых фильмов"""
    reset_queries()  # Сброс запросов для отладки
    
    movies = Movie.objects.filter(
        poster__isnull=False,
        average_rating__gte=8.0  # Добавляем фильтр по рейтингу
    ).prefetch_related(
        'genres'
    ).order_by('-average_rating')
    
    # Отладочная информация
    logger.debug(f"Featured movies count: {movies.count()}")
    for movie in movies:
        logger.debug(f"Movie: {movie.title}, Rating: {movie.average_rating}, Status: {movie.status}")
    
    # Выводим SQL запрос
    logger.debug(f"SQL Query: {movies.query}")
    
    return {'featured_movies': movies}

@register.inclusion_tag('showcase/widgets/current_movies.html')
def show_current_movies():
    """Виджет для отображения текущих фильмов"""
    movies = Movie.objects.filter(
        poster__isnull=False,
        status='now'
    ).order_by('-release_date')
    
    logger.debug(f"Current movies count: {movies.count()}")
    return {'current_movies': movies}

@register.inclusion_tag('showcase/widgets/upcoming_movies.html')
def show_upcoming_movies():
    """Виджет для отображения предстоящих фильмов"""
    movies = Movie.objects.filter(
        poster__isnull=False,
        status='soon'
    ).order_by('release_date')
    
    logger.debug(f"Upcoming movies count: {movies.count()}")
    return {'upcoming_movies': movies}

@register.inclusion_tag('showcase/widgets/streaming_services.html')
def show_streaming_services():
    """Виджет для отображения онлайн-кинотеатров"""
    online_cinemas = OnlineCinema.objects.all()
    return {'streaming_services': online_cinemas}

@register.inclusion_tag('showcase/widgets/genres_sidebar.html', takes_context=True)
def show_genres_sidebar(context):
    """Виджет для отображения сайдбара с жанрами"""
    genres = Genre.objects.annotate(
        movie_count=Count('movies'),
        avg_rating=Avg('movies__average_rating')
    )
    return {
        'genres': genres,
        'current_genre': context.get('current_genre')
    }

@register.inclusion_tag('showcase/tags/movie_genres.html', takes_context=True)
def show_genres_with_counts(context):
    """Показывает список жанров с количеством фильмов"""
    genres = Genre.objects.annotate(
        movie_count=Count('movies'),
        avg_rating=Avg('movies__average_rating')
    )
    return {
        'genres': genres,
        'current_genre': context.get('current_genre')
    }

@register.simple_tag
def get_trending_movies(days=7, limit=5):
    """Возвращает популярные фильмы за последние дни"""
    return Movie.objects.filter(
        status='now'
    ).annotate(
        rating_count=Count('movierating')
    ).filter(
        rating_count__gt=0
    ).order_by('-average_rating')[:limit]

@register.simple_tag
def total_movies():
    """Возвращает общее количество фильмов"""
    return Movie.objects.count()

@register.inclusion_tag('showcase/tags/latest_movies.html')
def show_latest_movies(count=5):
    """Показывает последние фильмы"""
    latest_movies = Movie.objects.filter(
        status='now'
    ).order_by('-release_date')[:count]
    return {'latest_movies': latest_movies}

@register.simple_tag(takes_context=True)
def user_recommendations(context, count=5):
    """Возвращает рекомендованные фильмы для пользователя"""
    user = context['request'].user
    if user.is_authenticated:
        # Получаем жанры, которые нравятся пользователю
        favorite_genres = Movie.objects.filter(
            movierating__user=user, 
            movierating__rating__gte=7
        ).values_list('genres__id', flat=True)
        
        # Рекомендуем фильмы этих жанров
        return Movie.objects.filter(
            genres__id__in=favorite_genres
        ).exclude(
            movierating__user=user
        ).distinct()[:count]
    return Movie.objects.none() 