from django.contrib import admin

from .models import Ingredient


# @admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    # Поля, отображаемые в списке
    list_display = ('name', 'measurement_unit')
    # Поля для поиска
    search_fields = ('name',)
    # Фильтр по первой букве названия (для удобства)
    list_filter = ('name',)


admin.site.register(Ingredient, IngredientAdmin)
