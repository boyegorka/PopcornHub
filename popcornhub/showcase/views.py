from rest_framework import viewsets
from rest_framework.decorators import action, api_view
from rest_framework import status
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from django.core.cache import cache
from termcolor import colored  # Добавим цветной вывод для наглядности
from rest_framework.response import Response
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib import messages
from datetime import timedelta
from django.contrib.admin.views.decorators import staff_member_required

from .mixins import CacheMixin

from django.db.models import Q, Avg, Count

from .pagination import CustomPagination  # Импортируем кастомную пагинацию
from .models import (
    Movie, Cinema, Showtime, Actor, Genre, Favorite, MovieRating,
    OnlineCinema, MovieOnlineCinema
)
from .serializers import (
    MovieSerializer, CinemaSerializer, ShowtimeSerializer, ActorSerializer,
    GenreSerializer, FavoriteSerializer, MovieRatingSerializer,
    OnlineCinemaSerializer, MovieOnlineCinemaSerializer
)
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .forms import MovieForm, CustomUserCreationForm, CustomAuthenticationForm


# Фильтры для фильмов
class MovieFilter(filters.FilterSet):
    release_date_start = filters.DateFilter(field_name='release_date', lookup_expr='gte')
    release_date_end = filters.DateFilter(field_name='release_date', lookup_expr='lte')
    min_duration = filters.NumberFilter(field_name='duration', lookup_expr='gte')

    class Meta:
        model = Movie
        fields = ['release_date_start', 'release_date_end', 'min_duration']


# Фильтры для кинотеатров
class CinemaFilter(filters.FilterSet):
    address_contains = filters.CharFilter(field_name='address', lookup_expr='icontains')

    class Meta:
        model = Cinema
        fields = ['address_contains']


# Фильтры для сеансов
class ShowtimeFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name='ticket_price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='ticket_price', lookup_expr='lte')
    date = filters.DateFilter(field_name='start_time', lookup_expr='date')

    class Meta:
        model = Showtime
        fields = ['min_price', 'max_price', 'date']


@extend_schema_view(
    list=extend_schema(
        description='Получить список фильмов',
        parameters=[
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                description='Поиск по названию или описанию'
            ),
            OpenApiParameter(
                name='release_date_start',
                type=OpenApiTypes.DATE,
                description='Фильтр по дате релиза (начало)'
            ),
            OpenApiParameter(
                name='release_date_end',
                type=OpenApiTypes.DATE,
                description='Фильтр по дате релиза (конец)'
            ),
        ],
        responses={200: MovieSerializer(many=True)}
    ),
    retrieve=extend_schema(
        description='Получить детальную информацию о фильме',
        responses={200: MovieSerializer}
    ),
    create=extend_schema(
        description='Создать новый фильм',
        request=MovieSerializer,
        responses={201: MovieSerializer}
    ),
    update=extend_schema(
        description='Обновить информацию о фильме',
        request=MovieSerializer,
        responses={200: MovieSerializer}
    ),
    destroy=extend_schema(
        description='Удалить фильм',
        responses={204: None}
    )
)
class MovieViewSet(CacheMixin, viewsets.ModelViewSet):
    """ViewSet для работы с фильмами."""
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ['title', 'description']
    filterset_class = MovieFilter

    @action(methods=['GET'], detail=False, url_path='latest')
    def latest_movies(self, request):
        """Получить последние фильмы в прокате"""
        movies = Movie.objects.filter(
            status='now'
        ).order_by('-release_date')[:5]
        serializer = self.get_serializer(movies, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='recommendations')
    def user_recommendations(self, request):
        """Получить рекомендации для пользователя"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Получаем жанры, которые нравятся пользователю
        favorite_genres = Movie.objects.filter(
            movierating__user=request.user, 
            movierating__rating__gte=7
        ).values_list('genres__id', flat=True)
        
        # Рекомендуем фильмы этих жанров
        movies = Movie.objects.filter(
            genres__id__in=favorite_genres
        ).exclude(
            movierating__user=request.user
        ).distinct()[:5]
        
        serializer = self.get_serializer(movies, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='not-rated')
    def not_rated(self, request):
        """Получить фильмы, которые пользователь еще не оценил"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        movies = Movie.objects.exclude(
            movierating__user=request.user
        ).order_by('-release_date')
        
        return self.get_paginated_response(
            self.get_serializer(
                self.paginate_queryset(movies), 
                many=True
            ).data
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Дата для фильтрации'
            )
        ],
        responses={200: MovieSerializer(many=True)}
    )
    @action(methods=['GET'], detail=False, url_path='released-before')
    def released_before(self, request):
        """Получить фильмы, выпущенные до указанной даты"""
        release_date = request.query_params.get('date')
        if not release_date:
            return Response({'error': 'date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        movies = self.queryset.filter(release_date__lte=release_date)
        serializer = self.get_serializer(movies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 2. Получить фильмы с длительностью более указанного значения
    @action(methods=['GET'], detail=False, url_path='long-duration')
    def long_duration(self, request):
        duration = request.query_params.get('duration', 120)  # Значение по умолчанию 120 минут
        movies = self.queryset.filter(duration__gte=duration)
        serializer = self.get_serializer(movies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 3. Обновить только название фильма (для конкретного объекта)
    @action(methods=['POST'], detail=True, url_path='update-title')
    def update_title(self, request, pk=None):

        movie = self.get_object()
        new_title = request.data.get('title')
        if not new_title:
            return Response({'error': 'title is required'}, status=status.HTTP_400_BAD_REQUEST)
        movie.title = new_title
        movie.save()
        return Response({'message': 'Title updated successfully'}, status=status.HTTP_200_OK)

    def get_queryset(self):
        return Movie.objects.select_related(
            'director'
        ).prefetch_related(
            'genres',
            'actors',
            Prefetch('movierating_set', queryset=MovieRating.objects.select_related('user'))
        )

    @action(methods=['GET'], detail=False, url_path='search-movies')
    def search_movies(self, request):

        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        movies = Movie.objects.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)  # ИЛИ по описанию
        )
        serializer = self.get_serializer(movies, many=True)
        return Response(serializer.data)

    # Фильтрация фильмов по сложным условиям
    @action(methods=['GET'], detail=False, url_path='complex-filter')
    def complex_filter(self, request):

        cache_key = f'movie_complex_filter_{request.query_params.urlencode()}'
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            message = colored('✨ Результаты фильтрации получены из КЕША Redis', 'green', attrs=['bold'])
            print('\n' + '=' * 50)
            print(message)
            print(f'Cache key: {cache_key}')
            print('=' * 50 + '\n')
            return Response(cached_result, status=status.HTTP_200_OK)
        message = colored('🔄 Выполняется фильтрация из БАЗЫ ДАННЫХ', 'yellow', attrs=['bold'])
        print('\n' + '=' * 50)
        print(message)
        print(f'Cache key: {cache_key}')
        print('=' * 50 + '\n')
        min_duration = request.query_params.get('min_duration', 90)
        max_duration = request.query_params.get('max_duration', 150)
        exclude_word = request.query_params.get('exclude_word', 'boring')
        release_year = request.query_params.get('release_year')
        query = (
            Q(duration__gte=min_duration) & Q(duration__lte=max_duration)
            & (Q(title__icontains='action') | Q(title__icontains='drama'))
            & ~Q(description__icontains=exclude_word)
        )
        if release_year:
            query &= Q(release_date__year=release_year)
        movies = self.queryset.filter(query)
        serializer = self.get_serializer(movies, many=True)
        # Кешируем результат на 30 минут
        cache.set(cache_key, serializer.data, timeout=1800)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):

        movie = serializer.save()
        # Отправляем уведомление асинхронно через Celery
        send_movie_notification.delay(
            movie.title,
            'admin@example.com'  # Можно заменить на список email'ов подписчиков
        )

    @action(methods=['GET'], detail=False, url_path='trending')
    def trending_movies(self, request):
        """Возвращает популярные фильмы"""
        movies = Movie.objects.filter(
            status='now'
        ).annotate(
            rating_count=Count('movierating')
        ).filter(
            rating_count__gt=0
        ).order_by('-average_rating')[:5]
        
        serializer = self.get_serializer(movies, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False, url_path='by-genre')
    def movies_by_genre(self, request):
        """Группировка фильмов по жанрам с подсчетом"""
        genres = Genre.objects.annotate(
            movie_count=Count('movies'),
            avg_rating=Avg('movies__average_rating')
        )
        
        data = [{
            'genre': genre.name,
            'movie_count': genre.movie_count,
            'average_rating': genre.avg_rating
        } for genre in genres]
        
        return Response(data)
    
    @action(methods=['GET'], detail=False)
    def exclude_genres(self, request):
        genre_ids = request.query_params.getlist('genres')
        queryset = Movie.objects.exclude(genres__id__in=genre_ids)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
            
        except EmptyPage:
            return Response({
                'error': 'Page number is out of range',
                'results': []
            }, status=status.HTTP_404_NOT_FOUND)
        except PageNotAnInteger:
            return Response({
                'error': 'Invalid page number',
                'results': []
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}',
                'results': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ViewSet для модели Cinema
class CinemaViewSet(viewsets.ModelViewSet):
    queryset = Cinema.objects.all()
    serializer_class = CinemaSerializer
    pagination_class = CustomPagination  # Применяем нашу кастомную пагинацию
    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ['name', 'address']
    filterset_class = CinemaFilter

    # 4. Получить кинотеатры, находящиеся на определённой улице
    @action(methods=['GET'], detail=False, url_path='by-street')
    def by_street(self, request):
        street = request.query_params.get('street')
        if not street:
            return Response({'error': 'street parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        cinemas = self.queryset.filter(address__icontains=street)
        serializer = self.get_serializer(cinemas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 5. Обновить адрес конкретного кинотеатра
    @action(methods=['POST'], detail=True, url_path='update-address')
    def update_address(self, request, pk=None):

        cinema = self.get_object()
        new_address = request.data.get('address')
        if not new_address:
            return Response({'error': 'address is required'}, status=status.HTTP_400_BAD_REQUEST)
        cinema.address = new_address
        cinema.save()
        return Response({'message': 'Address updated successfully'}, status=status.HTTP_200_OK)

    def get_queryset(self):

        queryset = super().get_queryset()
        category = self.kwargs.get('category')  # Получаем именованный аргумент из URL
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    @action(methods=['GET'], detail=False, url_path='search-cinemas')
    def search_cinemas(self, request):

        query = request.query_params.get('q', '')
        exclude_district = request.query_params.get('exclude_district', '')
        cinemas = Cinema.objects.filter(
            (Q(name__icontains=query) | Q(address__icontains=query))
            & ~Q(address__icontains=exclude_district)
        )
        serializer = self.get_serializer(cinemas, many=True)
        return Response(serializer.data)


# ViewSet для модели Showtime
class ShowtimeViewSet(viewsets.ModelViewSet):
    queryset = Showtime.objects.all()
    serializer_class = ShowtimeSerializer
    pagination_class = CustomPagination  # Применяем нашу кастомную пагинацию
    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ['movie__title', 'cinema__name']
    filterset_class = ShowtimeFilter

    # 6. Получить сеансы, которые начнутся в определённый день
    @action(methods=['GET'], detail=False, url_path='on-date')
    def on_date(self, request):

        date = request.query_params.get('date')
        if not date:
            return Response(
                {'error': 'date parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cache_key = f'showtime_date_{date}'
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            message = colored('✨ Расписание получено из КЕША Redis', 'green', attrs=['bold'])
            print('\n' + '=' * 50)
            print(message)
            print(f'Cache key: {cache_key}')
            print('=' * 50 + '\n')
            showtimes = self.queryset.filter(start_time__date=date)
            serializer = self.get_serializer(showtimes, many=True)
            # Кешируем результат на 15 минут
            cache.set(cache_key, serializer.data, timeout=900)
            return Response(serializer.data, status=status.HTTP_200_OK)
        message = colored('🔄 Расписание загружается из БАЗЫ ДАННЫХ', 'yellow', attrs=['bold'])
        print('\n' + '=' * 50)
        print(message)
        print(f'Cache key: {cache_key}')
        print('=' * 50 + '\n')
        showtimes = self.queryset.filter(start_time__date=date)
        serializer = self.get_serializer(showtimes, many=True)
        # Кешируем результат на 15 минут
        cache.set(cache_key, serializer.data, timeout=900)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 7. Обновить цену билета для конкретного сеанса
    @action(methods=['POST'], detail=True, url_path='update-ticket-price')
    def update_ticket_price(self, request, pk=None):

        showtime = self.get_object()
        new_price = request.data.get('ticket_price')
        if not new_price:
            return Response({'error': 'ticket_price is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            showtime.ticket_price = float(new_price)
            showtime.save()
            return Response({'message': 'Ticket price updated successfully'}, status=status.HTTP_200_OK)
        except ValueError:
            return Response({'error': 'Invalid price format'}, status=status.HTTP_400_BAD_REQUEST)

    # Сложная фильтрация сеансов
    @action(methods=['GET'], detail=False, url_path='filter-complex')
    def filter_complex(self, request):

        min_price = request.query_params.get('min_price', 10)
        max_price = request.query_params.get('max_price', 50)
        exclude_cinema = request.query_params.get('exclude_cinema', 'Unknown')
        # Пример сложного запроса:
        # (Сеансы с ценой билета между min_price и max_price) И
        # (Сеансы в кинотеатре, содержащем в названии 'Grand' или 'Plaza') И
        # НЕ в кинотеатре с названием exclude_cinema
        query = (
            Q(ticket_price__gte=min_price)
            & Q(ticket_price__lte=max_price)
            & (Q(cinema__name__icontains='Grand') | Q(cinema__name__icontains='Plaza'))
            & ~Q(cinema__name__iexact=exclude_cinema)
        )
        showtimes = self.queryset.filter(query)
        serializer = self.get_serializer(showtimes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['GET'],
        detail=False,
        url_path='search-showtimes'
    )
    def search_showtimes(self, request):
        min_price = request.query_params.get('min_price', 0)
        max_price = request.query_params.get('max_price', 100000)
        time_after = request.query_params.get('time_after')
        query = (
            Q(ticket_price__gte=min_price)
            & Q(ticket_price__lte=max_price)
        )
        if time_after:
            query &= Q(start_time__gte=time_after)
        showtimes = Showtime.objects.filter(query)
        serializer = self.get_serializer(showtimes, many=True)
        return Response(serializer.data)


# ViewSet для модели Actor
class ActorViewSet(CacheMixin, viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter]
    search_fields = ['name', 'biography']  # Добавляем поле для поиска

    @action(methods=['GET'], detail=False, url_path='by-movie')
    def by_movie(self, request):

        movie_id = request.query_params.get('movie_id')
        if not movie_id:
            return Response({'error': 'movie_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        actors = self.queryset.filter(movies__id=movie_id)
        serializer = self.get_serializer(actors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='search-actors')
    def search_actors(self, request):

        name = request.query_params.get('name', '')
        min_birth_year = request.query_params.get('min_birth_year')
        max_birth_year = request.query_params.get('max_birth_year')
        query = Q(name__icontains=name)
        if min_birth_year:
            query &= Q(date_of_birth__year__gte=min_birth_year)
        if max_birth_year:
            query &= Q(date_of_birth__year__lte=max_birth_year)
        actors = Actor.objects.filter(query)
        serializer = self.get_serializer(actors, many=True)
        return Response(serializer.data)


# ViewSet для модели Genre
class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ['name']

    @action(methods=['GET'], detail=False, url_path='by-movie')
    def by_movie(self, request):

        movie_id = request.query_params.get('movie_id')
        if not movie_id:
            return Response({'error': 'movie_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        genres = self.queryset.filter(movies__id=movie_id)
        serializer = self.get_serializer(genres, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ViewSet для модели Favorite
class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ['movie__title', 'user__username']

    def get_queryset(self):
        # Фильтруем избранное только для текущего пользователя
        return Favorite.objects.filter(user=self.request.user)

    @action(methods=['POST'], detail=False, url_path='toggle')
    def toggle_favorite(self, request):

        movie_id = request.data.get('movie_id')
        if not movie_id:
            return Response(
                {'error': 'movie_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite = Favorite.objects.filter(
            user=request.user,
            movie_id=movie_id
        ).first()
        if favorite:
            favorite.delete()
            return Response(
                {'message': 'Removed from favorites'},
                status=status.HTTP_200_OK
            )
        else:
            Favorite.objects.create(user=request.user, movie_id=movie_id)
            return Response(
                {'message': 'Added to favorites'},
                status=status.HTTP_201_CREATED
            )


# ViewSet для модели MovieRating
class MovieRatingViewSet(CacheMixin, viewsets.ModelViewSet):
    queryset = MovieRating.objects.all()
    serializer_class = MovieRatingSerializer

    def get_queryset(self):

        queryset = super().get_queryset()
        return self.get_cached_queryset(queryset)

    @action(methods=['GET'], detail=False, url_path='user-ratings')
    def user_ratings(self, request):

        ratings = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='movie-average')
    def movie_average(self, request):

        movie_id = request.query_params.get('movie_id')
        if not movie_id:
            return Response(
                {'error': 'movie_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cache_key = f'movie_rating_{movie_id}'
        avg_rating = cache.get(cache_key)
        if avg_rating is None:
            avg_rating = MovieRating.objects.filter(movie_id=movie_id).aggregate(
                Avg('rating'))['rating__avg']
            if avg_rating is not None:
                cache.set(cache_key, avg_rating, timeout=3600)
        return Response({'average': avg_rating}, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='search-ratings')
    def search_ratings(self, request):
        min_rating = request.query_params.get('min_rating', 1)
        max_rating = request.query_params.get('max_rating', 10)
        movie_title = request.query_params.get('movie_title', '')
        ratings = MovieRating.objects.filter(
            Q(rating__gte=min_rating)
            & Q(rating__lte=max_rating)
            & Q(movie__title__icontains=movie_title)
        )
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description='Получить список онлайн-кинотеатров'),
    retrieve=extend_schema(description='Получить детальную информацию об онлайн-кинотеатре'),
    create=extend_schema(description='Добавить новый онлайн-кинотеатр'),
    update=extend_schema(description='Обновить информацию об онлайн-кинотеатре'),
    destroy=extend_schema(description='Удалить онлайн-кинотеатр')
)
class OnlineCinemaViewSet(viewsets.ModelViewSet):
    queryset = OnlineCinema.objects.all()
    serializer_class = OnlineCinemaSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ['name', 'url']

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='movie_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID фильма для поиска платформ'
            )
        ],
        description='Получить список онлайн-кинотеатров для конкретного фильма'
    )
    @action(methods=['GET'], detail=False, url_path='by-movie')
    def by_movie(self, request):
        """Получить список онлайн-кинотеатров для конкретного фильма"""
        movie_id = request.query_params.get('movie_id')
        if not movie_id:
            return Response(
                {'error': 'movie_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        online_cinemas = self.queryset.filter(
            movieonlinecinema__movie_id=movie_id)
        serializer = self.get_serializer(online_cinemas, many=True)
        return Response(serializer.data)

@extend_schema_view(
    list=extend_schema(description='Получить список связей фильмов с онлайн-кинотеатрами'),
    retrieve=extend_schema(description='Получить детальную информацию о связи'),
    create=extend_schema(description='Создать новую связь'),
    update=extend_schema(description='Обновить связь'),
    destroy=extend_schema(description='Удалить связь')
)
class MovieOnlineCinemaViewSet(viewsets.ModelViewSet):
    queryset = MovieOnlineCinema.objects.all()
    serializer_class = MovieOnlineCinemaSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ['movie__title', 'online_cinema__name']

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='movie_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID фильма для поиска доступных платформ'
            )
        ],
        description='Получить список доступных платформ для конкретного фильма'
    )
    @action(methods=['GET'], detail=False, url_path='available-platforms')
    def available_platforms(self, request):
        """Получить список доступных платформ для конкретного фильма"""
        movie_id = request.query_params.get('movie_id')
        if not movie_id:
            return Response(
                {'error': 'movie_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        platforms = self.queryset.filter(movie_id=movie_id)
        serializer = self.get_serializer(platforms, many=True)
        return Response(serializer.data)


# Регистрация нового пользователя
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация успешна!")
            return redirect('showcase:index')
        else:
            messages.error(request, "Ошибка при регистрации. Пожалуйста, проверьте данные.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# Профиль пользователя с избранными фильмами
@login_required
def profile(request):
    # Получаем избранные фильмы
    favorite_movies = Movie.objects.filter(movie_favorites__user=request.user)
    
    # Получаем все оценки пользователя
    user_ratings = MovieRating.objects.filter(
        user=request.user
    ).select_related('movie').order_by('-id')  # Сортируем по id, так как created_at пока нет
    
    context = {
        'favorite_movies': favorite_movies,
        'user_ratings': user_ratings,
    }
    return render(request, 'showcase/profile.html', context)

# Защищенное представление для добавления фильма в избранное
class AddToFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        Favorite.objects.get_or_create(user=request.user, movie=movie)
        return redirect('movie-detail', pk=pk)

@api_view(['GET'])
def movie_detail_view(request, movie_id):
    """API endpoint для получения деталей фильма"""
    movie = get_object_or_404(
        Movie.objects.prefetch_related('actors'),  # Убедимся, что актеры загружаются
        id=movie_id
    )
    serializer = MovieSerializer(movie)
    print("API Response:", serializer.data)  # Добавим отладочный вывод
    return Response(serializer.data)

def index(request):
    featured_movies = Movie.objects.filter(
        status='now',
        poster__isnull=False
    ).order_by('-average_rating')[:5]
    
    context = {
        'featured_movies': featured_movies,
    }
    return render(request, 'showcase/index.html', context)

@staff_member_required
def movie_create(request):
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            movie = form.save()
            messages.success(request, 'Фильм успешно добавлен!')
            return redirect('showcase:movie-detail', pk=movie.pk)
    else:
        form = MovieForm()
    
    return render(request, 'showcase/movie_form.html', {
        'form': form,
        'title': 'Добавление нового фильма'
    })

def movie_update(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES, instance=movie)
        if form.is_valid():
            movie = form.save()
            return HttpResponseRedirect(reverse('showcase:movie-detail', args=[movie.id]))
    else:
        form = MovieForm(instance=movie)
    
    return render(request, 'showcase/movie_form.html', {
        'form': form,
        'movie': movie
    })

@staff_member_required
def movie_delete(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    
    if request.method == 'POST':
        title = movie.title
        movie.delete()
        messages.success(request, f'Фильм "{title}" был успешно удален.')
        return redirect('showcase:movie-list')
        
    return redirect('showcase:movie-detail', pk=pk)

@staff_member_required
def get_movie_stats(request):
    # Получаем общую статистику
    total_movies = Movie.objects.count()
    avg_rating = Movie.objects.aggregate(Avg('average_rating'))['average_rating__avg']
    avg_duration = Movie.objects.aggregate(Avg('duration'))['duration__avg']

    # Получаем статистику по статусам
    stats = Movie.objects.values('status').annotate(
        count=Count('id'),
        avg_rating=Avg('average_rating'),
        avg_duration=Avg('duration')
    )

    # Получаем топ жанров
    top_genres = Genre.objects.annotate(
        movie_count=Count('movies')
    ).order_by('-movie_count')[:5]

    context = {
        'total_movies': total_movies,
        'avg_rating': avg_rating,
        'avg_duration': avg_duration,
        'stats': stats,
        'top_genres': top_genres,
    }
    
    return render(request, 'showcase/movie_stats.html', context)

@staff_member_required
def bulk_status_update(request):
    if request.method == 'POST':
        # Обновляем все фильмы старше 90 дней
        old_movies = Movie.objects.filter(
            release_date__lt=timezone.now() - timedelta(days=90),
            status='now'
        )
        updated = old_movies.update(status='end')
        
        messages.success(request, f'Successfully updated {updated} movies.')
        return redirect('showcase:movie-list')
    
    return render(request, 'showcase/bulk_update.html')

def advanced_movie_search(request):
    # Chaining filters с использованием __contains и __icontains
    query = request.GET.get('q', '')
    genre = request.GET.get('genre', '')
    
    movies = Movie.objects.all()
    
    if query:
        movies = movies.filter(
            Q(title__icontains=query) |  # Нечувствительный к регистру поиск
            Q(description__contains=query)  # Чувствительный к регистру поиск
        )
    
    if genre:
        movies = movies.filter(genres__name__icontains=genre)
    
    # Limiting QuerySets
    movies = movies[:50]  # Ограничиваем результат 50 фильмами
    
    # values_list() пример
    movie_titles = movies.values_list('title', flat=True)
    
    # count() пример
    total_count = movies.count()
    
    # exists() пример
    has_results = movies.exists()
    
    context = {
        'movies': movies,
        'movie_titles': movie_titles,
        'total_count': total_count,
        'has_results': has_results,
        'query': query,
        'genre': genre
    }
    
    return render(request, 'showcase/movie_search.html', context)

def batch_operations(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_movies')
        
        if selected_ids:
            # Получаем QuerySet с выбранными фильмами
            selected_movies = Movie.objects.filter(id__in=selected_ids)
            
            if action == 'update_status':
                # update() пример
                new_status = request.POST.get('new_status')
                updated = selected_movies.update(status=new_status)
                messages.success(request, f'Updated {updated} movies')
            
            elif action == 'delete':
                # delete() пример
                deleted_count = selected_movies.delete()[0]
                messages.success(request, f'Deleted {deleted_count} movies')
    
    return redirect('showcase:movie-list')

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Добро пожаловать, {username}!")
                return redirect('showcase:index')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "Вы успешно вышли из системы!")
    return redirect('showcase:index')

@login_required
def profile_view(request):
    online_cinemas = OnlineCinema.objects.all()
    return render(request, 'showcase/profile.html', {
        'user': request.user,
        'online_cinemas': online_cinemas
    })

def movie_actors(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    actors = [{"name": actor.name} for actor in movie.actors.all()]
    return JsonResponse({"actors": actors})

@login_required
def rate_movie(request, movie_id):
    if request.method == 'POST':
        movie = get_object_or_404(Movie, id=movie_id)
        rating_value = int(request.POST.get('rating', 0))
        if 1 <= rating_value <= 10:
            # Создаем или обновляем оценку
            rating, created = MovieRating.objects.update_or_create(
                user=request.user,
                movie=movie,
                defaults={'rating': rating_value}
            )
            
            # Пересчитываем среднюю оценку фильма
            avg_rating = MovieRating.objects.filter(movie=movie).aggregate(Avg('rating'))['rating__avg']
            movie.average_rating = avg_rating or 0
            movie.total_ratings = MovieRating.objects.filter(movie=movie).count()
            movie.save()
            
            messages.success(request, 'Ваша оценка сохранена!')
        else:
            messages.error(request, 'Некорректная оценка')
    return redirect('showcase:movie-detail', pk=movie_id)

@login_required
def add_to_favorite(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    if request.method == 'POST':
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            movie=movie
        )
        if not created:
            favorite.delete()
            messages.success(request, 'Фильм удален из избранного')
        else:
            messages.success(request, 'Фильм добавлен в избранное')
    return redirect('showcase:movie-detail', pk=movie_id)

def movie_detail(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    # Получаем отсортированных актеров
    movie_actors = movie.movieactor_set.all().order_by('-is_main_role')
    # Получаем только будущие сеансы
    showtimes = movie.showtime_set.filter(
        start_time__gte=timezone.now()
    ).select_related('cinema').order_by('start_time')
    
    context = {
        'movie': movie,
        'movie_actors': movie_actors,
        'showtimes': showtimes,
    }
    return render(request, 'showcase/movie_detail.html', context)

@login_required
def delete_rating(request, rating_id):
    if request.method == 'POST':
        rating = get_object_or_404(MovieRating, id=rating_id, user=request.user)
        movie = rating.movie
        rating.delete()
        
        # Пересчитываем среднюю оценку фильма
        avg_rating = MovieRating.objects.filter(movie=movie).aggregate(Avg('rating'))['rating__avg']
        movie.average_rating = avg_rating or 0
        movie.total_ratings = MovieRating.objects.filter(movie=movie).count()
        movie.save()
        
        messages.success(request, 'Оценка удалена')
    return redirect('showcase:profile')

def movie_list(request):
    query = request.GET.get('q', '')
    movies = Movie.objects.all().order_by('-release_date')
    
    if query:
        movies = movies.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    
    context = {
        'movies': movies,
        'query': query
    }
    return render(request, 'showcase/movie_list_all.html', context)
