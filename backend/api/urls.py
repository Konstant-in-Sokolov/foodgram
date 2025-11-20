from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import CustomUserViewSet
from recipes.views import RecipeViewSet
from tags.views import TagViewSet
from ingredients.views import IngredientViewSet


router = DefaultRouter()

router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')


# urlpatterns = [
#     path('', include(router.urls)),
#     path('', include('djoser.urls')),
#     path('auth/', include('djoser.urls.authtoken')),
#     path(
#         'users/me/avatar/',
#         CustomUserViewSet.as_view(
#             {'put': 'avatar', 'delete': 'delete_avatar'}
#         ),
#         name='user-avatar'
#     ),
# ]


# user_patterns = [
#     # Полный путь: /api/users/subscriptions/
#     path(
#         'subscriptions/',
#         CustomUserViewSet.as_view({'get': 'list'}),
#         name='subscriptions'
#     ),
#     # Полный путь: /api/users/me/avatar/
#     path(
#         'me/avatar/',
#         CustomUserViewSet.as_view(
#             {'put': 'avatar', 'delete': 'delete_avatar'}
#         ),
#         name='user-avatar'
#     ),
# ]

# urlpatterns = [
#     path('users/', include(user_patterns)),
#     path('', include(router.urls)),
#     path('', include('djoser.urls')),
#     path('auth/', include('djoser.urls.authtoken')),
#     path('', include(router.urls)),
# ]

urlpatterns = [
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

    # path(
    #     'users/subscriptions/',
    #     CustomUserViewSet.as_view({'get': 'list'}),
    #     name='subscriptions'
    # ),

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
