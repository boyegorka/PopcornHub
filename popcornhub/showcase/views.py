from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from django.core.cache import cache
from termcolor import colored  # Добавим цветной вывод для наглядности
from rest_framework.response import Response

from .mixins import CacheMixin

from django.db.models import Q, Avg

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


# ViewSet для модели Movie
class MovieViewSet(CacheMixin, viewsets.ModelViewSet):
    queryset = Movie.objects.all()  # Получаем все фильмы
    serializer_class = MovieSerializer  # Используем сериализатор для фильмов
    pagination_class = CustomPagination  # Применяем нашу кастомную пагинацию
    filter_backends = [SearchFilter, filters.DjangoFilterBackend]  # Подключаем фильтрацию
    search_fields = ['title', 'description']  # Поля для поиска
    filterset_class = MovieFilter  # Подключаем фильтр

    # 1. Получить фильмы, выпущенные до указанной даты
    @action(methods=['GET'], detail=False, url_path='released-before')
    def released_before(self, request):

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

        queryset = super().get_queryset()
        title = self.request.query_params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)
        return self.get_cached_queryset(queryset)

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
            return Response(cached_result, status=status.HTTP_200_OK)
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


# ViewSet для модели OnlineCinema
class OnlineCinemaViewSet(viewsets.ModelViewSet):
    queryset = OnlineCinema.objects.all()
    serializer_class = OnlineCinemaSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ['name', 'url']

    @action(methods=['GET'], detail=False, url_path='by-movie')
    def by_movie(self, request):

        movie_id = request.query_params.get('movie_id')
        if not movie_id:
            return Response(
                {'error': 'movie_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        online_cinemas = self.queryset.filter(
            movieonlinecinema__movie_id=movie_id)
        serializer = self.get_serializer(online_cinemas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='search-platforms')
    def search_platforms(self, request):

        query = request.query_params.get('q', '')
        exclude_domain = request.query_params.get('exclude_domain', '')
        platforms = OnlineCinema.objects.filter(
            (Q(name__icontains=query) | Q(url__icontains=query))
            & ~Q(url__icontains=exclude_domain)
        )
        serializer = self.get_serializer(platforms, many=True)
        return Response(serializer.data)


# ViewSet для модели MovieOnlineCinema
class MovieOnlineCinemaViewSet(viewsets.ModelViewSet):
    queryset = MovieOnlineCinema.objects.all()
    serializer_class = MovieOnlineCinemaSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ['movie__title', 'online_cinema__name']

    @action(methods=['GET'], detail=False, url_path='available-platforms')
    def available_platforms(self, request):

        movie_id = request.query_params.get('movie_id')
        if not movie_id:
            return Response(
                {'error': 'movie_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        platforms = self.queryset.filter(movie_id=movie_id)
        serializer = self.get_serializer(platforms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
