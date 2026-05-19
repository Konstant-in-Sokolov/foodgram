from django.http import Http404
from django.shortcuts import redirect
from rest_framework.decorators import api_view

from recipes.models import Recipe


@api_view(('GET',))
def recipe_short_redirect(request, pk):
    """Обрабатывает короткую ссылку и перенаправляет на фронтенд сайта."""
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404(f'id={pk} рецепт не найден.')

    host = request.get_host()
    protocol = (
        'https' if not host.startswith('127.0.0.1')
        and not host.startswith('localhost') else 'http'
    )

    return redirect(f'{protocol}://{host}/recipes/{pk}/')
