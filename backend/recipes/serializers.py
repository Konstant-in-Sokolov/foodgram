from rest_framework import serializers
from django.db import transaction
from django.conf import settings
from .models import Recipe, IngredientInRecipe
from ingredients.models import Ingredient
from tags.models import Tags
# =========================================================================
# 1. Сериализаторы для записи (POST/PATCH) - Обрабатывают входящие данные
# =========================================================================


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    # Принимаем ID ингредиента
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    # Валидация количества
    amount = serializers.IntegerField(
        min_value=1,
        max_value=32000,
        error_messages={'min_value': 'Количество должно быть не менее 1.'}
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(),
        many=True
    )
    # Принимает Base64-изображение (или файл)
    image = serializers.ImageField(max_length=None, use_url=True)

    cooking_time = serializers.IntegerField(
        min_value=1,
        error_messages={
            'min_value': 'Время приготовления должно быть не менее 1 минуты.'
        }
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        )

    # --- Вспомогательный метод для создания/обновления связей ---
    def create_ingredients_and_tags(self, ingredients, tags, recipe):
        # Создание связей ингредиентов
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            ) for item in ingredients
        ])
        # Установка тегов
        recipe.tags.set(tags)

    # --- Валидация ---
    def validate(self, data):
        ingredients = data.get('ingredients')
        tags = data.get('tags')

        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Добавьте хотя бы один ингредиент.'}
            )

        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )

        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Добавьте хотя бы один тег.'}
            )

        return data

    # --- Создание рецепта ---
    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )

        self.create_ingredients_and_tags(ingredients, tags, recipe)
        return recipe

    # --- Обновление рецепта ---
    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        # Обновление основных полей
        super().update(instance, validated_data)

        # Удаляем старые связи и создаем новые
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients_and_tags(ingredients, tags, instance)

        return instance

# =========================================================================
# 2. Сериализаторы для чтения (GET) - Форматируют исходящие данные
# =========================================================================


class IngredientReadSerializer(serializers.ModelSerializer):
    # Поля ингредиента из Ingredient
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    ingredients = IngredientReadSerializer(
        source='ingredient_amounts', # related_name из IngredientInRecipe
        many=True,
        read_only=True
    )
    tags = serializers.SlugRelatedField(
        many=True,
        slug_field='slug',
        queryset=Tags.objects.all()
    )
    # Автор должен отображаться в формате для чтения (например, username)
    author = serializers.ReadOnlyField(source='author.username')

    # Расчетные поля (пока возвращают False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        # Будет реализовано после создания модели "Избранное"
        return False

    def get_is_in_shopping_cart(self, obj):
        # Будет реализовано после создания модели "Списки покупок"
        return False
