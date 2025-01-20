from django import forms
from .models import Movie, Cinema, MovieRating

class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = ['title', 'description', 'release_date', 'duration', 'poster', 'genres']
        widgets = {
            'release_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

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