from django.contrib import admin
from django.db.models import Count

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
    list_filter = ('author', 'tags', 'name')
    search_fields = ('name', 'author__username', 'tags__name', 'author__email')

    inlines = (IngredientInRecipeInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(fav_count=Count('in_favorites'))

    @admin.display(description='В избранном', ordering='fav_count')
    def in_favorites_count(self, obj):
        return obj.fav_count
