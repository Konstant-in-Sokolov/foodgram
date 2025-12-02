from django.contrib import admin

from .models import IngredientInRecipe, Recipe


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'author', 'cooking_time', 'pub_date', 'in_favorites_count'
    )
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('author', 'tags', 'name')

    inlines = (IngredientInRecipeInline,)

    def in_favorites_count(self, obj):
        return 0
