import base64
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy
from djoser.serializers import UserSerializer as DjoserUserSerializer
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.shared_serializers import ShortRecipeSerializer
# from .models import Subscription


User = get_user_model()


class CustomUserSerializer(DjoserUserSerializer):
    """
    Стандартный сериализатор пользователя, наследуется от Djoser.
    Используется для регистрации, /users/me/ и /users/{id}/.
    """

    class Meta:
        model = User
        # Добавьте все поля, которые должны быть видны
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name'
        )
        # Поля для чтения
        read_only_fields = ('email', 'username')


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


class FollowListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )
        read_only_fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return Subscription.objects.filter(
            follower=request.user, following=obj
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        context = {'request': request}
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                raise serializers.ValidationError(
                    gettext_lazy('recipe_limit must be integer'),
                )
        recipes = obj.recipe_set.all()[:recipes_limit]
        return ShortRecipeSerializer(
            recipes, many=True, context=context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipe_set.count()


# class FollowSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Subscription
#         fields = ('follower', 'following')
#         validators = [
#             UniqueTogetherValidator(
#                 queryset=Subscription.objects.all(),
#                 fields=fields,
#                 message=gettext_lazy(
#                     'You are already subscribed to this author'
#                 ),
#             )
#         ]

    # def validate(self, data):
    #     request = self.context.get('request')
    #     following = data['following']
    #     if request.user == following:
    #         raise serializers.ValidationError(
    #             gettext_lazy('You can not subscribe to yourself'),
    #         )
    #     return data

    # def to_representation(self, instance):
    #     request = self.context.get('request')
    #     context = {'request': request}
    #     return FollowListSerializer(
    #         instance.following, context=context
    #     ).data


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
