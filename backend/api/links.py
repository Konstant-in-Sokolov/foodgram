from django.http import Http404
from django.shortcuts import redirect
from rest_framework.decorators import api_view

from recipes.models import Recipe


@api_view(('GET',))
def recipe_short_redirect(request, pk):
    """Обрабатывает короткую ссылку и перенаправляет на полный URL."""
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404(f'id={pk} рецепт не найден.')
    return redirect(f'/recipes/{pk}/')
