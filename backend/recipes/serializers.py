from django.db import transaction
from rest_framework import serializers

from recipes.fields import Base64ImageField
from tags.serializers import TagSerializer
from users.serializers import UserReadSerializer

from .models import Ingredient, IngredientInRecipe, Recipe, Tag


class IngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи ингредиентов."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')

    def validate_amount(self, value):
        """Проверяет, что количество ингредиента > 0."""
        if value <= 0:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше нуля!'
            )
        return value


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов с количеством."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    # amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и отображения рецептов."""
    author = UserReadSerializer(read_only=True)
    image = Base64ImageField(required=True)

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
            'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = ('pub_date',)

    def validate(self, data):
        """Валидация данных."""
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError('Обязательное поле.')

        # проверка на уникальность
        ingredient_ids = [
            ingredient['id'] for ingredient in ingredients
        ]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не могут повторяться.'
            )
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Необходимо выбрать хотя бы один тег.'}
            )
        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                {'tags': 'Теги не могут повторяться.'}
            )
        return data

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
        """Формируем ответ для фронтенда."""
        rep = super().to_representation(instance)
        rep['ingredients'] = rep.pop('read_ingredients')
        rep['tags'] = TagSerializer(instance.tags.all(), many=True).data
        return rep

    def add_ingredients(self, ingredients_data, recipe):
        """Сохраняем ингредиенты с количеством."""
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            ) for item in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        data_for_creation = validated_data.copy()

        ingredients_data = data_for_creation.pop('ingredients', [])
        tags_data = data_for_creation.pop('tags', [])

        data_for_creation.pop('author', None)
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **data_for_creation)

        if tags_data:
            recipe.tags.set(tags_data)
        if ingredients_data:
            self.add_ingredients(ingredients_data, recipe)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):

        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)

        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            instance.ingredient_amounts.all().delete()
            self.add_ingredients(ingredients_data, instance)

        return super().update(instance, validated_data)
