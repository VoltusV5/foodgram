"""Настройки пагинации API."""

from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Пагинация с настраиваемым лимитом."""

    page_size = 6
    page_size_query_param = 'limit'
