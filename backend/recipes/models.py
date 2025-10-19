from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
# from django.conf import settings # Используем AUTH_USER_MODEL
from django.db import models

# Получаем кастомную модель пользователя
# User = settings.AUTH_USER_MODEL
from ingredients.models import Ingredient
from tags.models import Tags


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
        upload_to='recipes/images/'  # Указываем папку для загрузки
    )
    text = models.TextField(
        'Описание'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                1, message='Время приготовления должно быть не менее 1 минуты.'
            )
        ]
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    # Связи с другими моделями
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',  # Связь через вспомогательную модель
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tags,
        related_name='recipes',
        verbose_name='Теги'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']  # Сортировка от новых к старым
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'name'],
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
        on_delete=models.PROTECT, # Запрет удаления ингредиента, если он используется
        related_name='ingredient_amounts',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(1, message='Количество должно быть не менее 1.')
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        # Уникальность: один и тот же ингредиент
        # может быть в одном рецепте только один раз.
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} – {self.amount}'
            f'{self.ingredient.measurement_unit}'
        )
