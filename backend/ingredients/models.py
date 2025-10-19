from django.db import models


class Ingredient(models.Model):
    """Модель ингридиентов для рецептов."""

    name = models.CharField(
        'Название',
        max_length=200,
        unique=True
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=50
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        # Обеспечиваем, что название и единица измерения уникальны вместе
        # (например, "Соль" (гр) и "Соль" (щепотка) — разные записи,
        # но "Мука" (гр) уникальна).
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_unit'
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'
