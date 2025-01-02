from .models import Movie, Cinema, Showtime, Actor, Genre, Favorite, MovieRating, OnlineCinema, MovieOnlineCinema
from .serializers import MovieSerializer, CinemaSerializer, ShowtimeSerializer, ActorSerializer, GenreSerializer, FavoriteSerializer, MovieRatingSerializer, OnlineCinemaSerializer, MovieOnlineCinemaSerializer
from rest_framework import viewsets
from .pagination import CustomPagination  # Импортируем кастомную пагинацию
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from django.db.models import Q, Avg
from .tasks import send_email_task




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
class MovieViewSet(viewsets.ModelViewSet):
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
            return Response({"error": "date parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
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
            return Response({"error": "title is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        movie.title = new_title
        movie.save()
        return Response({"message": "Title updated successfully"}, status=status.HTTP_200_OK)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        title = self.request.query_params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)
        return queryset
    
    # Фильтрация фильмов по сложным условиям
    @action(methods=['GET'], detail=False, url_path='complex-filter')
    def complex_filter(self, request):
        min_duration = request.query_params.get('min_duration', 90)
        max_duration = request.query_params.get('max_duration', 150)
        exclude_word = request.query_params.get('exclude_word', 'boring')
        release_year = request.query_params.get('release_year')

        # Пример сложного запроса: 
        # (Фильмы с длительностью между min_duration и max_duration) И 
        # (в названии содержится слово 'action' или 'drama') И 
        # НЕ содержат слово exclude_word в описании
        # Если указан release_year, фильтруем по году выхода
        query = (
            Q(duration__gte=min_duration) & Q(duration__lte=max_duration) &
            (Q(title__icontains='action') | Q(title__icontains='drama')) &
            ~Q(description__icontains=exclude_word)
        )
        if release_year:
            query &= Q(release_date__year=release_year)

        movies = self.queryset.filter(query)
        serializer = self.get_serializer(movies, many=True)
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
            return Response({"error": "street parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        cinemas = self.queryset.filter(address__icontains=street)
        serializer = self.get_serializer(cinemas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 5. Обновить адрес конкретного кинотеатра
    @action(methods=['POST'], detail=True, url_path='update-address')
    def update_address(self, request, pk=None):
        cinema = self.get_object()
        new_address = request.data.get('address')
        if not new_address:
            return Response({"error": "address is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        cinema.address = new_address
        cinema.save()
        return Response({"message": "Address updated successfully"}, status=status.HTTP_200_OK)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.kwargs.get('category')  # Получаем именованный аргумент из URL
        if category:
            queryset = queryset.filter(category=category)
        return queryset


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
        # send_email_task.delay()
        date = request.query_params.get('date')
        if not date:
            return Response({"error": "date parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        showtimes = self.queryset.filter(start_time__date=date)
        serializer = self.get_serializer(showtimes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 7. Обновить цену билета для конкретного сеанса
    @action(methods=['POST'], detail=True, url_path='update-ticket-price')
    def update_ticket_price(self, request, pk=None):
        showtime = self.get_object()
        new_price = request.data.get('ticket_price')
        if not new_price:
            return Response({"error": "ticket_price is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            showtime.ticket_price = float(new_price)
            showtime.save()
            return Response({"message": "Ticket price updated successfully"}, status=status.HTTP_200_OK)
        except ValueError:
            return Response({"error": "Invalid price format"}, status=status.HTTP_400_BAD_REQUEST)
        
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
            Q(ticket_price__gte=min_price) & Q(ticket_price__lte=max_price) &
            (Q(cinema__name__icontains='Grand') | Q(cinema__name__icontains='Plaza')) &
            ~Q(cinema__name__iexact=exclude_cinema)
        )

        showtimes = self.queryset.filter(query)
        serializer = self.get_serializer(showtimes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ViewSet для модели Actor
class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ['first_name', 'last_name']

    @action(methods=['GET'], detail=False, url_path='by-movie')
    def by_movie(self, request):
        movie_id = request.query_params.get('movie_id')
        if not movie_id:
            return Response({"error": "movie_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        actors = self.queryset.filter(movies__id=movie_id)
        serializer = self.get_serializer(actors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
            return Response({"error": "movie_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
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
            return Response({"error": "movie_id is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        favorite = Favorite.objects.filter(user=request.user, 
                                         movie_id=movie_id).first()
        if favorite:
            favorite.delete()
            return Response({"message": "Removed from favorites"}, 
                          status=status.HTTP_200_OK)
        else:
            Favorite.objects.create(user=request.user, movie_id=movie_id)
            return Response({"message": "Added to favorites"}, 
                          status=status.HTTP_201_CREATED)

# ViewSet для модели MovieRating
class MovieRatingViewSet(viewsets.ModelViewSet):
    queryset = MovieRating.objects.all()
    serializer_class = MovieRatingSerializer
    pagination_class = CustomPagination
    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ['movie__title', 'user__username']

    @action(methods=['GET'], detail=False, url_path='user-ratings')
    def user_ratings(self, request):
        ratings = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='movie-average')
    def movie_average(self, request):
        movie_id = request.query_params.get('movie_id')
        if not movie_id:
            return Response({"error": "movie_id is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Try to get rating from cache first
        cache_key = f'movie_rating_{movie_id}'
        avg_rating = cache.get(cache_key)
        
        if avg_rating is None:
            # If not in cache, calculate and cache it
            avg_rating = MovieRating.objects.filter(movie_id=movie_id).aggregate(
                Avg('rating'))['rating__avg']
            if avg_rating is not None:
                cache.set(cache_key, avg_rating, timeout=60*60)  # Cache for 1 hour
        
        return Response({"average": avg_rating}, status=status.HTTP_200_OK)

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
            return Response({"error": "movie_id is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        online_cinemas = self.queryset.filter(
            movieonlinecinema__movie_id=movie_id)
        serializer = self.get_serializer(online_cinemas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            return Response({"error": "movie_id is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        platforms = self.queryset.filter(movie_id=movie_id)
        serializer = self.get_serializer(platforms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
