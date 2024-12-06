from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MovieViewSet, CinemaViewSet, ShowtimeViewSet

router = DefaultRouter()
router.register(r'movies', MovieViewSet)
router.register(r'cinemas', CinemaViewSet)
router.register(r'showtimes', ShowtimeViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]