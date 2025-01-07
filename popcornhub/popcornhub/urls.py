"""
URL configuration for popcornhub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include  # include для маршрутов приложений
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter

from showcase.views import (
    MovieViewSet,
    CinemaViewSet,
    ShowtimeViewSet,
    ActorViewSet,
    GenreViewSet,
    FavoriteViewSet,
    MovieRatingViewSet,
    OnlineCinemaViewSet,
    MovieOnlineCinemaViewSet,
)

router = DefaultRouter()
router.register(r'movies', MovieViewSet)
router.register(r'cinemas', CinemaViewSet)
router.register(r'showtimes', ShowtimeViewSet)
router.register(r'actors', ActorViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'favorites', FavoriteViewSet)
router.register(r'ratings', MovieRatingViewSet)
router.register(r'online-cinemas', OnlineCinemaViewSet)
router.register(r'movie-online-cinemas', MovieOnlineCinemaViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),  # Админка
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Добавляем маршруты для медиафайлов в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.index_title = settings.ADMIN_INDEX_TITLE
