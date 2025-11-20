from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponse, Http404

from rest_framework.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, IsAuthenticated
)
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view

from .models import Recipe, Favorite
from .serializers import RecipeSerializer, IngredientInRecipe
from users.serializers import AuthorSerializer


User = get_user_model()


@api_view(['GET'])
def recipe_short_redirect(request, pk):
    """Обрабатывает короткую ссылку и перенаправляет на полный URL."""
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404(f'id={pk} рецепт не найден.')
    return redirect(f'/recipes/{pk}/')


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для Рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        # 1. Получаем базовый queryset
        queryset = super().get_queryset()
        user = self.request.user

        # --- ФИЛЬТРАЦИЯ ПО ТЕГАМ ---
        tags_slugs = self.request.query_params.getlist('tags')

        if tags_slugs:
            queryset = queryset.filter(tags__slug__in=tags_slugs).distinct()

        # --- ФИЛЬТРАЦИЯ ПО ИЗБРАННОМУ И СПИСКУ ПОКУПОК ---
        if user.is_authenticated and self.request.query_params.get(
            'is_favorited'
        ) == '1':
            queryset = queryset.filter(in_favorites__user=user)

        if user.is_authenticated and self.request.query_params.get(
            'is_in_shopping_cart'
        ) == '1':
            queryset = queryset.filter(in_shopping_cart__user=user)

        # --- ФИЛЬТРАЦИЯ ПО АВТОРУ ---
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author__id=author_id)

        return queryset.order_by('-pub_date')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """
        Обрабатывает добавление и удаление рецепта в/из избранного.
        """
        recipe = self.get_object()
        user = request.user

        # Добавить в избранное.
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            return Response(
                {'message': 'Рецепт добавлен в избранное.'},
                status=status.HTTP_201_CREATED
            )

        # Удалить из избранного.
        elif request.method == 'DELETE':
            favorite_instance = Favorite.objects.filter(
                user=user, recipe=recipe
            )
            if not favorite_instance.exists():
                return Response(
                    {'errors': 'Рецепта нет в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request):
        """
        Объединяет все ингредиенты из рецептов в списке покупок пользователя
        и возвращает их в виде текстового файла.
        """
        user = request.user

        # 1. Фильтрация и агрегация
        ingredients = IngredientInRecipe.objects.filter(
            recipe__in_shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        # 2. Формирование списка
        shopping_list = []
        for item in ingredients:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['total_amount']
            shopping_list.append(f'{name} ({unit}) — {amount}')

        # 3. Создание текстового ответа (response)
        content = '\n'.join(shopping_list)

        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """Генерирует короткую ссылку для рецепта."""
        if not Recipe.objects.filter(pk=pk).exists():
            raise ValidationError(f'id={pk} рецепт не найден.')
        return Response({
            'short-link': request.build_absolute_uri(
                reverse('recipe_short_link', args=[pk])
            )
        })


class SubscriptionPagination(PageNumberPagination):
    """
    Пагинация для списка подписок.
    """
    page_size = 6
    page_size_query_param = 'limit'


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для отображения списка авторов, на которых подписан пользователь.
    Соответствует маршруту /api/users/subscriptions/
    """
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)
