from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'showcase'

urlpatterns = [
    # showcase URLs
    path('movies/<int:movie_id>/', views.movie_detail_view, name='movie-detail'),
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password-change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
]
