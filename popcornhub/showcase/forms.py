from django import forms
from .models import Movie, Cinema, MovieRating, Genre
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class MovieForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        help_text='Введите описание фильма'
    )
    
    genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        help_text='Выберите жанры фильма'
    )
    
    poster = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text='Загрузите постер фильма'
    )

    class Meta:
        model = Movie
        fields = ['title', 'description', 'release_date', 'duration', 'genres', 'poster', 'status']
        exclude = ['average_rating']
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'release_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        
        labels = {
            'title': 'Название фильма',
            'release_date': 'Дата выхода',
            'duration': 'Продолжительность (минуты)',
            'status': 'Статус показа',
        }
        
        error_messages = {
            'title': {
                'required': 'Пожалуйста, введите название фильма',
                'max_length': 'Название слишком длинное'
            },
            'duration': {
                'required': 'Укажите продолжительность фильма',
                'invalid': 'Введите корректное число'
            }
        }

    class Media:
        css = {
            'all': ('css/movie-form.css',)
        }
        js = ('js/movie-form.js',)

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) < 3:
            raise forms.ValidationError("Название должно содержать минимум 3 символа")
        return title

    def save(self, commit=True):
        movie = super().save(commit=False)
        if commit:
            movie.save()
            self.save_m2m()  # Сохраняем связи many-to-many
        return movie 

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Имя пользователя'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Подтвердите пароль'})
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Имя пользователя'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'})
    ) 