from django.db import transaction
from rest_framework import serializers

from .models import Recipe, Tag, Ingredient, IngredientInRecipe
from tags.serializers import TagSerializer
from ingredients.serializers import IngredientSerializer
from recipes.fields import Base64ImageField
from users.serializers import AuthorSerializer, SubscribedUserSerializer


class IngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи Ингредиентов"""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов и их количества в рецепте."""

    # Поля ингредиента
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    # Поле количества (Amount)
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для записи Рецептов."""

    author = AuthorSerializer(read_only=True)
    ingredients = IngredientWriteSerializer(
        many=True,
        write_only=True
    )
    read_ingredients = serializers.SerializerMethodField()
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        write_only=True,
        required=True
    )
    tags = serializers.SerializerMethodField()
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'author', 'image', 'text',
            'tags', 'tag_ids',
            'ingredients', 'read_ingredients',
            'cooking_time', 'pub_date',
            'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = ('pub_date',)

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Проверяем наличие записи в модели Favorite
            # для текущего пользователя и рецепта.
            return obj.in_favorites.filter(user=request.user).exists()
        return False

    # 3. Метод для вывода ингредиентов (заменяет старый read_only)
    def get_read_ingredients(self, obj):
        """Возвращает список ингредиентов для GET-запроса."""
        return IngredientInRecipeSerializer(
            obj.ingredient_amounts.all(),
            many=True,
            context=self.context
        ).data

    def get_tags(self, obj):
        # Используем TagSerializer для сериализации объектов Tag
        return TagSerializer(obj.tags.all(), many=True).data

    # 4. Переименование поля read_ingredients обратно в ingredients для вывода
    def to_representation(self, instance):
        """Переименовывает поле для соответствия фронтенду."""
        representation = super().to_representation(instance)
        # Переименовываем 'read_ingredients' обратно в 'ingredients'
        representation['ingredients'] = representation.pop('read_ingredients')
        return representation

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Проверяем наличие записи в модели ShoppingCart
            # для текущего пользователя и рецепта.
            return obj.in_shopping_cart.filter(user=request.user).exists()
        return False

    # Вспомогательная функция для сохранения ингредиентов
    def add_ingredients(self, ingredients_data, recipe):
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            ) for item in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        # 1. Извлекаем M2M данные для ручной обработки
        tags_data = validated_data.pop('tags', [])
        # tags_data = validated_data.pop('tag_ids', [])
        ingredients_data = validated_data.pop('ingredients', [])

        # 2. Создаем основной объект
        recipe = Recipe.objects.create(**validated_data)

        # 3. Сохраняем M2M связи
        if tags_data:
            recipe.tags.set(tags_data)
        if ingredients_data:
            self.add_ingredients(ingredients_data, recipe)

        return recipe
