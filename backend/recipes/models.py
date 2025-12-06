from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from ingredients.models import Ingredient
from tags.models import Tag

MIN_VALUE = 1
MAX_VALUE = 600

User = get_user_model()


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        'Название',
        max_length=256,
        unique=True
    )
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/images/'
    )
    text = models.TextField(
        'Описание'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                MIN_VALUE,
                message=(
                    f'Время приготовления должно быть не менее '
                    f'{MIN_VALUE} минуты.'
                )
            ),
            MaxValueValidator(
                MAX_VALUE,
                message=(
                    f'Время приготовления не может превышать '
                    f'{MAX_VALUE} минут.'
                )
            )
        ]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'name'),
                name='unique_author_recipe'
            )
        ]

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Модель для связи Рецепт к Ингредиент с указанием количества."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_amounts',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name='ingredient_amounts',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                MIN_VALUE,
                message=f'Количество должно быть не менее {MIN_VALUE}.'
            ),
            MaxValueValidator(
                MAX_VALUE,
                message=f'Количество не может превышать {MAX_VALUE}.'
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} – {self.amount}'
            f'{self.ingredient.measurement_unit}'
        )


class Favorite(models.Model):
    """Модель для хранения избранных рецептов пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='in_favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_recipe'
            )
        ]

    def __str__(self):
        return f'{self.user.username} добавил "{self.recipe.name}" в избранное'


class ShoppingCart(models.Model):
    """Модель для хранения рецептов в списке покупок пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списке покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart_recipe'
            )
        ]

    def __str__(self):
        return (
            f'{self.user.username} добавил '
            f'"{self.recipe.name}" в список покупок.'
        )
