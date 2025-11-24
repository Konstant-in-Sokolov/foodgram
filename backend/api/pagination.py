from rest_framework.pagination import PageNumberPagination
from rest_framework.pagination import LimitOffsetPagination


class SubscriptionPagination(PageNumberPagination):
    """
    Пагинация для списка подписок.
    """
    page_size = 6
    page_size_query_param = 'limit'
