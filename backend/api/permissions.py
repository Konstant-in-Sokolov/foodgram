from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Кастомное разрешение для атвора и читателя.

    Разрешает:
    - Всем: GET, HEAD, OPTIONS (только чтение)
    - Владельцу объекта (автору): PUT, PATCH, DELETE.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_superuser
