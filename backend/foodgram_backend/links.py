from django.shortcuts import get_object_or_404, redirect
from rest_framework.decorators import api_view

from recipes.models import Recipe


@api_view(('GET',))
def recipe_short_redirect(request, pk):
    """Обрабатывает короткую ссылку и перенаправляет на фронтенд."""
    recipe = get_object_or_404(Recipe, pk=pk)
    return redirect(f'/recipes/{recipe.pk}/')
