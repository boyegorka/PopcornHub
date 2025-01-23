from django.urls import path
from . import views

app_name = 'showcase'

urlpatterns = [
    # Основные страницы
    path('', views.index, name='index'),
    
    # Аутентификация
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('api/movies/<int:movie_id>/actors/', views.movie_actors, name='movie-actors'),
    path('movies/<int:pk>/', views.movie_detail, name='movie-detail'),
    path('movies/<int:movie_id>/rate/', views.rate_movie, name='rate-movie'),
    path('movies/<int:movie_id>/favorite/', views.add_to_favorite, name='add-to-favorite'),
    path('ratings/<int:rating_id>/delete/', views.delete_rating, name='delete-rating'),
    path('api/movies/<int:movie_id>/', views.movie_detail_view, name='movie-detail-api'),
    path('movies/bulk-update/', views.bulk_status_update, name='movie-bulk-update'),
    path('movies/stats/', views.get_movie_stats, name='movie-stats'),
    path('movies/search/', views.advanced_movie_search, name='movie-search'),
    path('movies/batch/', views.batch_operations, name='batch-operations'),
    path('movies/<int:pk>/delete/', views.movie_delete, name='movie-delete'),
    path('movies/all/', views.movie_list, name='all-movies'),
    path('movies/create/', views.movie_create, name='movie-create'),
]
