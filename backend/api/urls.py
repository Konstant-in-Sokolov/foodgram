from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import CustomUserViewSet
from recipes.views import RecipeViewSet
from tags.views import TagViewSet
from ingredients.views import IngredientViewSet


router = DefaultRouter()
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users', CustomUserViewSet, basename='users')


urlpatterns = [
    path('', include(router.urls)),
    # path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
