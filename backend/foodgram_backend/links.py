from django.http import Http404
from django.shortcuts import redirect
from rest_framework.decorators import api_view

from recipes.models import Recipe


@api_view(('GET',))
def recipe_short_redirect(request, pk):
    """Обрабатывает короткую ссылку и перенаправляет на фронтенд."""
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404(f'id={pk} рецепт не найден.')

    host = request.get_host()
    local_hosts = ('127.0.0.1', 'localhost')

    if any(host.startswith(h) for h in local_hosts):
        protocol = 'http'
    else:
        protocol = 'https'

    base_url = protocol + '://' + host
    return redirect(f'{base_url}/recipes/{pk}/')
