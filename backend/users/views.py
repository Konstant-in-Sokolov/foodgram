from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from djoser.views import UserViewSet as DjoserUserViewSet

from .serializers import (
    AuthorSerializer,
    CustomUserSerializer,
    SubscribedUserSerializer,
    # RecipeShortSerializer,
    SubscriptionReadSerializer,
    AvatarSerializer
)
from .models import Subscription


User = get_user_model()


class SubscriptionPagination(PageNumberPagination):
    """
    Пагинация для списка подписок.
    """
    page_size = 6
    page_size_query_param = 'limit'


class CustomUserViewSet(DjoserUserViewSet):
    """
    ViewSet для управления пользователями и подписками.
    """

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SubscriptionPagination

    # Переопределяем метод, чтобы использовать SubscribedUserSerializer
    def get_serializer_class(self):
        if self.action == 'subscriptions':
            return SubscribedUserSerializer
        return CustomUserSerializer

    # Разрешения для стандартных действий:
    def get_permissions(self):
        if self.action == 'create':
            # Разрешаем создание (регистрацию) всем
            return [permissions.AllowAny()]
        # Остальные действия требуют аутентификации
        return super().get_permissions()

    # GET /api/users/subscriptions/
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        """
        Возвращает список авторов, на которых подписан текущий пользователь.
        """
        user = request.user
        authors = User.objects.filter(following__user=user)

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = AuthorSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionReadSerializer(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
        # return Response(serializer.data)

    # POST/DELETE /api/users/{id}/subscribe/
    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписка/отписка от автора."""
        author = self.get_object()
        user = request.user

        if author == user:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, author=author)

            serializer = SubscriptionReadSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                user=user, author=author
            ).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Вы не подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Обновление или удаление аватара пользователя."""
        user = request.user

        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user, data=request.data, partial=True, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


# class SubscriptionListViewSet(viewsets.ReadOnlyModelViewSet):
#     serializer_class = SubscriptionReadSerializer
#     permission_classes = (IsAuthenticated,)

#     def get_queryset(self):
#         return User.objects.filter(following__user=self.request.user)


# class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     ViewSet для отображения списка авторов, на которых подписан пользователь.
#     Соответствует маршруту /api/users/subscriptions/
#     """
#     serializer_class = AuthorSerializer
#     permission_classes = [IsAuthenticated]
#     pagination_class = SubscriptionPagination

#     def get_queryset(self):
#         return User.objects.filter(following__user=self.request.user)
