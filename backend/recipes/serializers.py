from rest_framework import serializers

from .models import Recipe, Ingredient


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('name', 'measurement_unit')


class RecipeSerializer(serializers.ModelSerializer):

    author = serializers.ReadOnlyField(source='author.username')
    ingredients = IngredientSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'author', 'image', 'text',
            'ingredients', 'cooking_time', 'pub_date'
        )
        read_only_fields = ('author', 'pub_date')
