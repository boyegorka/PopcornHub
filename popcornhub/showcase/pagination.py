from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.core.paginator import EmptyPage, PageNotAnInteger


class CustomPagination(PageNumberPagination):
    page_size = 10  # Количество объектов на странице по умолчанию
    page_size_query_param = 'page_size'  # Параметр в URL для указания количества объектов на странице
    max_page_size = 100  # Максимальный размер страницы

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view)
        except EmptyPage:
            # Если номер страницы больше, чем существует - возвращаем последнюю
            request.query_params._mutable = True
            request.query_params['page'] = self.page.paginator.num_pages
            request.query_params._mutable = False
            return super().paginate_queryset(queryset, request, view)
        except PageNotAnInteger:
            # Если передан некорректный номер страницы - возвращаем первую
            request.query_params._mutable = True
            request.query_params['page'] = 1
            request.query_params._mutable = False
            return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })
