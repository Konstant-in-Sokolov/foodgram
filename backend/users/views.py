from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (
    CustomUserSerializer,
    SubscribedUserSerializer,
    # RecipeShortSerializer
)


User = get_user_model()


class CustomUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями и подписками.
    Использует CustomUserSerializer для стандартных действий.
    """
    
    queryset = User.objects.all()
    
    serializer_class = CustomUserSerializer
    
    permission_classes = [permissions.IsAuthenticated]

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

    # -------------------------------------------------------------
    # Дополнительные @action для функционала Foodgram
    # -------------------------------------------------------------
    
    # GET /api/users/subscriptions/
    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        """Возвращает список авторов, на которых подписан текущий пользователь."""
        user = request.user
        # Предполагается, что у модели User есть related_name='follower' к Subscription
        authors = User.objects.filter(following__user=user)
        
        # Используем SubscribedUserSerializer с контекстом запроса
        serializer = SubscribedUserSerializer(
            authors, many=True, context={'request': request}
        )
        return self.get_paginated_response(self.paginate_queryset(serializer.data))

    # POST/DELETE /api/users/{id}/subscribe/
    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        """Подписка/отписка от автора."""
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
            # Логика подписки
            
            # Предполагается, что вы импортировали модель Subscription
            # if Subscription.objects.filter(user=user, author=author).exists():
            #     return Response(
            #         {'errors': 'Вы уже подписаны на этого автора.'}, 
            #         status=status.HTTP_400_BAD_REQUEST
            #     )
            # Subscription.objects.create(user=user, author=author)
            
            serializer = SubscribedUserSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            # Логика отписки
            
            # deleted, _ = Subscription.objects.filter(
            #     user=user, author=author
            # ).delete()
            # if deleted:
            #     return Response(status=status.HTTP_204_NO_CONTENT)
            # return Response(
            #     {'errors': 'Вы не подписаны на этого автора.'},
            #     status=status.HTTP_400_BAD_REQUEST
            # )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
