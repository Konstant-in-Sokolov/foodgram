import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy
from djoser.serializers import UserSerializer as DjoserUserSerializer
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.shared_serializers import ShortRecipeSerializer
from .models import Subscription
from recipes.models import Recipe
# from recipes.serializers import RecipeSerializer


User = get_user_model()


# class CustomUserSerializer(DjoserUserSerializer):
#     """
#     Стандартный сериализатор пользователя, наследуется от Djoser.
#     Используется для регистрации, /users/me/ и /users/{id}/.
#     """

#     class Meta:
#         model = User
#         # Добавьте все поля, которые должны быть видны
#         fields = (
#             'email', 'id', 'username', 'first_name', 'last_name'
#         )
#         # Поля для чтения
#         read_only_fields = ('email', 'username')


class CustomUserSerializer(DjoserUserCreateSerializer):

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )


class SubscribedUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            follower=request.user, following=obj
        ).exists()


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого отображения рецептов.
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class AuthorSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения автора подписки.
    """
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.following.filter(user=request.user).exists()
        return False

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        queryset = obj.recipes.all()

        if recipes_limit:
            try:
                limit = int(recipes_limit)
                queryset = queryset[:limit]
            except ValueError:
                pass

        return RecipeMinifiedSerializer(queryset, many=True).data


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для обработки Base64-изображений."""
    def to_internal_value(self, data):
        # Проверяем, если данные являются строкой Base64
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                # Декодируем строку Base64
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
            except Exception as e:
                raise serializers.ValidationError("Некорректный формат Base64-изображения.")

        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    # Используем кастомное поле для приема Base64-строки
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionReadSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения автора в списке подписок."""

    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        return True

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        queryset = obj.recipes.all()

        if recipes_limit and recipes_limit.isdigit():
            queryset = queryset[:int(recipes_limit)]

        return RecipeMinifiedSerializer(queryset, many=True).data
