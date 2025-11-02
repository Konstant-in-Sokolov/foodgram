from django.db import transaction
from rest_framework import serializers

from .models import Recipe, Tag, Ingredient, IngredientInRecipe
from ingredients.serializers import IngredientSerializer
from recipes.fields import Base64ImageField


class IngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи Ингредиентов"""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для записи Рецептов."""

    author = serializers.ReadOnlyField(source='author.id')
    ingredients = IngredientSerializer(many=True, read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True
    )
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'author', 'image', 'text', 'tags',
            'ingredients', 'cooking_time', 'pub_date',
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
        ingredients_data = validated_data.pop('ingredients', [])

        # 2. Создаем основной объект
        recipe = Recipe.objects.create(**validated_data)

        # 3. Сохраняем M2M связи
        if tags_data:
            recipe.tags.set(tags_data)
        if ingredients_data:
            self.add_ingredients(ingredients_data, recipe)

        return recipe
