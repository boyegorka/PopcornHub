from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def truncate_title(value, length=30):
    """Обрезает название фильма до указанной длины"""
    if len(value) > length:
        return value[:length] + '...'
    return value

@register.filter
def duration_format(minutes):
    """Форматирует длительность фильма из минут в часы и минуты"""
    hours = minutes // 60
    mins = minutes % 60
    return f'{hours}ч {mins:02d}мин'

@register.filter
def rating_stars(value):
    """Преобразует числовой рейтинг в звездочки"""
    try:
        rating = float(value)
        full_stars = '★' * int(rating)
        half_star = '½' if rating % 1 >= 0.5 else ''
        empty_stars = '☆' * (5 - int(rating) - (1 if half_star else 0))
        return f"{full_stars}{half_star}{empty_stars}"
    except (ValueError, TypeError):
        return "Нет оценки" 