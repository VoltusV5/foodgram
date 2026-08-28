"""Разрешения доступа."""

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Просмотр всем. CRUD только администраторам."""

    def has_permission(self, request, view):
        """Просмотр всем. CRUD только администраторам."""
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """
    Просмотр всем.

    Создание только авторизованным пользователям.
    Изменение и удаление — только автору или администратору.
    """

    def has_permission(self, request, view):
        """Проверяет право пользователя на работу с конкретным объектом."""
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        """Проверяет общее право взаимодействия с объектом."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            obj.author == request.user
            or request.user.is_staff
            or request.user.is_superuser
        )
