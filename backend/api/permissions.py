from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Кастомное разрешение, которое позволяет:
    - Всем: GET, HEAD, OPTIONS (только чтение)
    - Владельцу объекта (автору): PUT, PATCH, DELETE
    """

    def has_object_permission(self, request, view, obj):
        # Разрешение на чтение (GET, HEAD, OPTIONS) разрешено всем.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешение на запись (PUT, PATCH, DELETE) разрешено только:
        # 1. Владельцу объекта (если obj.author равен текущему пользователю).
        # 2. Суперпользователю (is_superuser).
        return obj.author == request.user or request.user.is_superuser
