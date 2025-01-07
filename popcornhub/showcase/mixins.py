from django.core.cache import cache
from termcolor import colored


class CacheMixin:
    def get_cache_key(self):
        """Генерация уникального ключа кеша"""
        return f'{self.__class__.__name__}_{self.request.query_params.urlencode()}'

    def get_cached_queryset(self, queryset):
        """Получение данных с использованием кеша"""
        cache_key = self.get_cache_key()
        # Пробуем получить результат из кеша
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            message = colored('✨ Данные получены из КЕША Redis', 'green', attrs=['bold'])
            print('\n' + '=' * 50)
            print(message)
            print(f'Cache key: {cache_key}')
            print('=' * 50 + '\n')
            return cached_result

        # Если в кеше нет, применяем фильтры
        message = colored('🔄 Данные загружены из БАЗЫ ДАННЫХ', 'yellow', attrs=['bold'])
        print('\n' + '=' * 50)
        print(message)
        print(f'Cache key: {cache_key}')
        print('=' * 50 + '\n')
        # Кешируем результат на 1 час
        cache.set(cache_key, queryset, timeout=3600)
        return queryset
