from django.contrib import admin

from .models import IngredientInRecipe, Recipe


class IngredientInRecipeInline(admin.TabularInline):
    # Связываем ингредиенты с рецептом (появится в форме редактирования Recipe)
    model = IngredientInRecipe
    extra = 1  # Дополнительное пустое поле для добавления
    min_num = 1  # Минимум один ингредиент


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'author', 'cooking_time', 'pub_date', 'in_favorites_count'
    )
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('author', 'tags', 'name')

    # Добавляем Inline для ингредиентов
    inlines = (IngredientInRecipeInline,)

    # Метод для подсчета, сколько раз рецепт добавлен в избранное
    def in_favorites_count(self, obj):
        # Этот функционал будет реализован после создания модели "Избранное"
        # Для начала, пусть возвращает 0 или заглушку
        return 0

    # in_favorites_count.short_description = 'В избранном'
