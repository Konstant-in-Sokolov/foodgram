from api.pagination import SubscriptionPagination
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.serializers import SubscriptionSerializer

from .models import Favorite, IngredientInRecipe, Recipe, ShoppingCart
from .serializers import RecipeSerializer

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
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        tags_slugs = self.request.query_params.getlist('tags')
        if tags_slugs:
            queryset = queryset.filter(tags__slug__in=tags_slugs).distinct()

        if user.is_authenticated:
            if self.request.query_params.get('is_favorited') == '1':
                queryset = queryset.filter(in_favorites__user=user)
            if self.request.query_params.get('is_in_shopping_cart') == '1':
                queryset = queryset.filter(in_shopping_cart__user=user)

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
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(user=user, recipe=recipe)
            return Response(
                {'message': 'Рецепт добавлен в избранное.'},
                status=status.HTTP_201_CREATED,
            )

        elif request.method == 'DELETE':
            favorite_instance = Favorite.objects.filter(
                user=user, recipe=recipe
            )
            if not favorite_instance.exists():
                return Response(
                    {'errors': 'Рецепта нет в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            return Response(
                {'message': 'Рецепт добавлен в корзину.'},
                status=status.HTTP_201_CREATED,
            )
        elif request.method == 'DELETE':
            cart_instance = ShoppingCart.objects.filter(
                user=user, recipe=recipe
            )
            if not cart_instance.exists():
                return Response(
                    {'errors': 'Рецепт не найден в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Скачать список ингредиентов из корзины."""
        user = request.user

        ingredients = (
            IngredientInRecipe.objects
            .filter(recipe__in_shopping_cart__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        shopping_list = [
            f'{item['ingredient__name']} '
            f'({item['ingredient__measurement_unit']}) — '
            f'{item['total_amount']}'
            for item in ingredients
        ]

        content = '\n'.join(shopping_list)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise ValidationError(f'id={pk} рецепт не найден.')
        return Response(
            {
                'short-link': request.build_absolute_uri(
                    reverse('recipe_short_link', args=[pk])
                )
            }
        )


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)
