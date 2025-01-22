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
    """
    Преобразует числовой рейтинг в HTML со звездочками
    value: float от 0 до 10
    """
    if value is None:
        value = 0
        
    # Преобразуем 10-балльную шкалу в 5-звездочную
    stars = value / 2
    
    full_stars = int(stars)  # Целые звезды
    half_star = stars - full_stars >= 0.5  # Есть ли половина звезды
    empty_stars = 5 - full_stars - (1 if half_star else 0)  # Пустые звезды
    
    html = []
    # Добавляем полные звезды
    for _ in range(full_stars):
        html.append('<i class="fa fa-star"></i>')
    
    # Добавляем половину звезды если есть
    if half_star:
        html.append('<i class="fa fa-star-half-o"></i>')
    
    # Добавляем пустые звезды
    for _ in range(empty_stars):
        html.append('<i class="fa fa-star-o"></i>')
        
    return mark_safe(''.join(html))

@register.filter
def rating_stars_10(value):
    """
    Преобразует числовой рейтинг в HTML со звездочками по 10-балльной шкале
    value: float от 0 до 10
    Все звезды видимы, заполненные звезды синего цвета
    """
    if value is None:
        value = 0
    
    html = []
    for i in range(10):
        if i < value:
            html.append('<i class="fa fa-star" style="color: #0054f7;"></i>')
        else:
            html.append('<i class="fa fa-star" style="color: #b3b3b3;"></i>')
    
    return mark_safe(''.join(html))

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