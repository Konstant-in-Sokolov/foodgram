import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import \
    UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.models import Recipe


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для декодирования картинки из строки Base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(
                    base64.b64decode(imgstr), name='temp.' + ext
                )
            except Exception:
                raise serializers.ValidationError(
                    "Некорректный формат изображения."
                )
        return super().to_internal_value(data)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Укороченная карточка рецепта (для списка подписок)."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор только для обновления аватарки."""
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserCreateSerializer(DjoserUserCreateSerializer):
    """Сериализатор для РЕГИСТРАЦИИ."""
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )


class UserReadSerializer(DjoserUserSerializer):
    """
    Сериализатор для ПРОСМОТРА пользователей (GET).
    Возвращает профиль + статус подписки + аватар.
    """
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        if request.user == obj:
            return False
        return obj.following.filter(user=request.user).exists()


class SubscriptionSerializer(UserReadSerializer):
    """Сериализатор для раздела ПОДПИСКИ."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except (ValueError, TypeError):
                pass
        return RecipeMinifiedSerializer(
            recipes, many=True, context={'request': request}
        ).data
