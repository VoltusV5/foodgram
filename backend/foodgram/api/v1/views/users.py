"""ViewSet'ы API для пользователей и подписок."""

from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from api.v1.pagination import CustomPagination
from api.v1.serializers.users import (AvatarSerializer, CustomUserSerializer,
                                      FollowSerializer,
                                      UserWithRecipesSerializer)
from recipes.models import Recipe
from users.models import Follow

UserModel = get_user_model()


class CustomUserViewSet(DjoserUserViewSet):
    """Вьюсет для обработки операций с пользователем."""

    queryset = UserModel.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    def get_permissions(self) -> list[BasePermission]:
        """Определяет разрешения для действия вьюсета.

        Returns:
            Список разрешений для текущего действия.
        """
        if self.action in ('me', 'avatar', 'set_password'):
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['put'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request: Request) -> Response:
        """Создает или обновляет аватар текущего пользователя.

        Args:
            request: Входящий HTTP-запрос.

        Returns:
            Ответ с данными обновленного пользователя.
        """
        user = request.user
        serializer = AvatarSerializer(
            user,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        if user.avatar:
            user.avatar.delete(save=False)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request: Request) -> Response:
        """Удаляет аватар текущего пользователя.

        Args:
            request: Входящий HTTP-запрос.

        Returns:
            Ответ без содержимого.
        """
        user = request.user
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request: Request) -> Response:
        """Возвращает пользователей, на которых подписан текущий пользователь.

        Args:
            request: Входящий HTTP-запрос.

        Returns:
            Пагинированные данные авторов.
        """
        authors = UserModel.objects.filter(
            following__user=request.user,
        ).annotate(
            recipes_count=Count('recipes', distinct=True),
        ).prefetch_related(
            Prefetch(
                'recipes',
                queryset=Recipe.objects.only(
                    'id', 'name', 'image', 'cooking_time', 'author_id',
                ),
            ),
        )

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True, context={'request': request},
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipesSerializer(
            authors, many=True, context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request: Request, **kwargs: object) -> Response:
        """Создает или удаляет подписку на пользователя.

        Args:
            request: Входящий HTTP-запрос.
            **kwargs: Параметры маршрута.

        Returns:
            Ответ с подпиской или статусом удаления.
        """
        author = self.get_object()

        if request.method == 'POST':
            serializer = FollowSerializer(
                data={
                    'user': request.user.id,
                    'author': author.id,
                },
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            deleted_count, _ = Follow.objects.filter(
                user=request.user, author=author,
            ).delete()

            if not deleted_count:
                return Response(
                    {'errors': 'Вы не подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
