"""Mixins для сериализаторов API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from recipes.models import Favorite, ShoppingCart
from rest_framework import serializers, status
from rest_framework.response import Response

if TYPE_CHECKING:
    from users.models import User


class SubscriptionCheckMixin(metaclass=serializers.SerializerMetaclass):
    """Добавляет статус подписки в сериализаторы с данными автора."""

    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj: User) -> bool:
        """Проверяет, подписан ли текущий пользователь на автора.

        Args:
            obj: Сериализуемый объект, представляющий автора.

        Returns:
            True, если текущий пользователь подписан на автора.
        """
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False

        if hasattr(obj, 'is_subscribed'):
            return obj.is_subscribed

        return request.user.following.filter(author=obj).exists()


class BaseRelationMixin:
    """Обрабатывает создание и удаление связей пользователя с рецептом."""

    def _manage_relation(
        self,
        model_class: type[Favorite] | type[ShoppingCart],
        serializer_class: type[serializers.Serializer],
    ) -> Response:
        """Создает или удаляет связь текущего пользователя с рецептом.

        Args:
            model_class: Django-модель.
            serializer_class: Сериализатор для проверки создания связи.
            pk: Первичный ключ из маршрута.

        Returns:
            Данные или статус удаления.
        """
        instance = self.get_object()
        user = self.request.user

        if self.request.method == 'POST':
            serializer = serializer_class(
                data={
                    'user': user.id,
                    'recipe': instance.id,
                },
                context={'request': self.request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted_count, _ = model_class.objects.filter(
            user=user, recipe=instance,
        ).delete()

        if not deleted_count:
            return Response(
                {'errors':
                 f'Объект отсутствует в {model_class._meta.verbose_name}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
