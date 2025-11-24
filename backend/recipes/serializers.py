from django.db import transaction
from rest_framework import serializers

from .models import Recipe, Tag, Ingredient, IngredientInRecipe
from tags.serializers import TagSerializer
from ingredients.serializers import IngredientSerializer
from recipes.fields import Base64ImageField
from users.serializers import SubscriptionSerializer, UserReadSerializer


class IngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи ингредиентов (валидация входных данных)."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов с количеством."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и отображения рецептов."""
    # author = SubscriptionSerializer(read_only=True)
    author = UserReadSerializer(read_only=True)
    image = Base64ImageField(required=True)

    # --- ИСПРАВЛЕНИЕ ТЕГОВ ---
    # 1. На вход принимаем ID (PrimaryKeyRelatedField)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    # Ингредиенты: на вход
    ingredients = IngredientWriteSerializer(many=True, write_only=True)
    # Ингредиенты: на выход
    read_ingredients = IngredientInRecipeSerializer(
        source='ingredient_amounts', many=True, read_only=True
    )

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'author', 'image', 'text',
            'tags', 'ingredients', 'read_ingredients',
            'cooking_time',
            # 'pub_date',
            'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = ('pub_date',)

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.in_favorites.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.in_shopping_cart.filter(user=request.user).exists()
        return False

    def to_representation(self, instance):
        """
        Формируем красивый ответ для фронтенда.
        """
        rep = super().to_representation(instance)

        # 1. Подменяем поле ingredients (убираем read_ingredients)
        rep['ingredients'] = rep.pop('read_ingredients')

        # 2. --- ИСПРАВЛЕНИЕ ТЕГОВ (НА ВЫХОД) ---
        # Подменяем список ID на список объектов тегов
        rep['tags'] = TagSerializer(instance.tags.all(), many=True).data

        return rep

    def add_ingredients(self, ingredients_data, recipe):
        """Сохраняем ингредиенты с количеством (bulk_create для скорости)."""
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            ) for item in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        tags_data = validated_data.pop('tags', []) # Тут теперь список объектов Tag (Django сам их нашел по ID)

        validated_data.pop('author', None)
        # Важно: добавляем автора из request
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)

        if tags_data:
            recipe.tags.set(tags_data)

        if ingredients_data:
            self.add_ingredients(ingredients_data, recipe)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        # Если поле не передали, ставим None, чтобы не стереть существующее случайно
        # (хотя pop с дефолтом [] сработает, но лучше проверить наличие ключа)

        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)

        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            instance.ingredient_amounts.all().delete()
            self.add_ingredients(ingredients_data, instance)

        # Обновляем остальные поля
        return super().update(instance, validated_data)
