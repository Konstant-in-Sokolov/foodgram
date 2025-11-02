from django.db.models import Sum
from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, IsAuthenticated
)
from rest_framework.response import Response

from .models import Recipe, Favorite
from .serializers import RecipeSerializer, IngredientInRecipe


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для Рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

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

        # --- 1. POST: Добавить в избранное ---
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

        # --- 2. DELETE: Удалить из избранного ---
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
    def download_shopping_cart(self, request):
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
