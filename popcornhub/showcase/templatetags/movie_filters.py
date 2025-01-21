from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

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
    if not minutes:
        return "N/A"
    hours = minutes // 60
    mins = minutes % 60
    return f'{hours}ч {mins:02d}мин'

@register.filter
def rating_stars(value):
    """Преобразует числовой рейтинг в звездочки"""
    try:
        rating = float(value)
        stars = ''
        for i in range(5):
            if rating >= i + 1:
                stars += '<i class="fa fa-star"></i>'
            elif rating > i:
                stars += '<i class="fa fa-star-half"></i>'
            else:
                stars += '<i class="fa fa-star-o"></i>'
        return mark_safe(stars)
    except (ValueError, TypeError):
        return ""

@register.filter(is_safe=True)
def stars_display(value):
    """Альтернативный вариант отображения звезд"""
    if not value:
        return "Нет оценки"
    try:
        rating = float(value)
        full_stars = int(rating)
        half_star = rating - full_stars >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        
        result = '★' * full_stars
        if half_star:
            result += '½'
        result += '☆' * empty_stars
        return result
    except (ValueError, TypeError):
        return "Нет оценки" 