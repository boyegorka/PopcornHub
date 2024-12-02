from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10  # Количество объектов на странице по умолчанию
    page_size_query_param = 'page_size'  # Параметр в URL для указания количества объектов на странице
    max_page_size = 100  # Максимальный размер страницы