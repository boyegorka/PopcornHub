from django import template
from django.db.models import Count, Avg
from ..models import Movie, Genre
from django.utils import timezone

register = template.Library()

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