from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.pagination import SubscriptionPagination
from api.serializers import (IngredientSerializer, RecipeSerializer,
                             SubscriptionSerializer, TagSerializer,
                             UserAvatarSerializer, UserReadSerializer)
from ingredients.models import Ingredient
from recipes.models import Favorite, IngredientInRecipe, Recipe, ShoppingCart
from tags.models import Tag
from users.models import Subscription

User = get_user_model()


class CustomUserViewSet(DjoserUserViewSet):
    """ViewSet для управления пользователями и подписками."""

    queryset = User.objects.all()
    pagination_class = SubscriptionPagination

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list', 'me']:
            return UserReadSerializer
        if self.action == 'subscriptions':
            return SubscriptionSerializer
        if self.action == 'subscribe':
            return SubscriptionSerializer
        if self.action == 'avatar':
            return UserAvatarSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ['retrieve', 'list']:  # Просмотр доступен всем
            return [permissions.AllowAny()]
        elif self.action == 'create':  # Регистрация доступна всем
            return [permissions.AllowAny()]
        # Для удаление/изменение/подписки нужна авторизация
        return [permissions.IsAuthenticated()]

    # GET /api/users/subscriptions/
    @action(
        detail=False,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Возвращает список авторов, на которых подписан текущий юзер."""

        user = request.user
        authors = User.objects.filter(following__user=user)

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = SubscriptionSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserReadSerializer(
            authors, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST/DELETE /api/users/{id}/subscribe/
    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        """Подписка/отписка от автора."""
        author = self.get_object()
        user = request.user

        if author == user:
            raise ValidationError(
                {'detail': 'Нельзя подписаться на самого себя'}
            )

        if request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                raise ValidationError(
                    {'errors': 'Вы уже подписаны на этого автора.'},
                )
            Subscription.objects.create(user=user, author=author)

            serializer = UserReadSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                user=user, author=author
            ).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise ValidationError(
                {'errors': 'Вы не подписаны на этого автора.'},
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('put', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Обновление или удаление аватара пользователя."""
        user = request.user

        if request.method == 'PUT':
            serializer = UserAvatarSerializer(
                user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для Рецептов."""

    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        queryset = Recipe.objects.all()
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

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
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
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
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
        methods=('get',),
        permission_classes=(IsAuthenticated,),
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
            (
                f'{item["ingredient__name"]} '
                f'{item["ingredient__measurement_unit"]} — '
                f'{item["total_amount"]}'
            ) for item in ingredients
        ]

        content = '\n'.join(shopping_list)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link'
    )
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
    permission_classes = (IsAuthenticated,)
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)
