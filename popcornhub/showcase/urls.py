from django.urls import path
from . import views

urlpatterns = [
    # showcase URLs
    path('movies/<int:movie_id>/', views.movie_detail_view, name='movie-detail'),
]
