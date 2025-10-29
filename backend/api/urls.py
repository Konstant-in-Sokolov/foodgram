from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import CustomUserViewSet
from recipes.views import RecipeViewSet
# from tags.views import TagViewSet
# from ingredients.views import IngredientViewSet


router = DefaultRouter()

router.register('recipes', RecipeViewSet, basename='recipes')
# router.register('tags', TagViewSet, basename='tags')
# router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users', CustomUserViewSet, basename='users')
# router.register(
#     'users/(?P<user_id>\d+)/subscribe',
#     SubscriptionViewSet,
#     basename='subscriptions'
# )


urlpatterns = [
    # Маршруты для регистрации/токенов (Djoser/кастомные)
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

    path(
        'users/me/avatar/',
        CustomUserViewSet.as_view({'put': 'avatar'}),
        name='user-avatar-upload'
    ),
    path(
        'users/me/avatar/',
        CustomUserViewSet.as_view({'delete': 'delete_avatar'}),
        name='user-avatar-delete'
    ),

    # Подключаем маршруты ViewSet'ов
    path('', include(router.urls)),
]
