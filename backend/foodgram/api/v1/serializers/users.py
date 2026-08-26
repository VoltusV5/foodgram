"""Сериализаторы пользователей, подписок и аватаров."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.v1.serializers.fields import Base64ImageField
from recipes.models import Favorite, Recipe, ShoppingCart
from users.models import Follow

from .mixins import SubscriptionCheckMixin

if TYPE_CHECKING:
    from users.models import User


UserModel = get_user_model()


class FollowData(TypedDict):
    """Описывает проверенные данные для создания подписки."""

    user: User
    author: User


class UserRecipeRelationData(TypedDict):
    """Описывает проверенные данные связи пользователя и рецепта."""

    user: User
    recipe: Recipe


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализует данные для регистрации нового пользователя."""

    class Meta:
        """Задает поля, используемые при регистрации пользователя."""

        model = UserModel
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class CustomUserSerializer(
        SubscriptionCheckMixin, serializers.ModelSerializer):
    """Сериализует публичные данные профиля пользователя."""

    avatar = Base64ImageField(read_only=True)

    class Meta:
        """Задает поля профиля пользователя и поля только для чтения."""

        model = UserModel
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

        read_only_fields = ('id', 'is_subscribed')


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализует данные для загрузки и обновления аватара пользователя."""

    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        """Задает поля сериализатора аватара."""

        model = UserModel
        fields = ('avatar',)


class FollowSerializer(serializers.ModelSerializer):
    """Сериализует создание и отображение подписки."""

    class Meta:
        """Задает поля связи подписки."""

        model = Follow
        fields = ('user', 'author')

    def validate(self, data: FollowData) -> FollowData:
        """Проверяет, что подписка может быть создана.

        Args:
            data: Входные данные подписки с пользователем и автором.

        Returns:
            Проверенные данные подписки.
        """
        user = data['user']
        author = data['author']
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя.',
            )
        if user.follower.filter(author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора.',
            )
        return data

    def to_representation(self, instance: Follow) -> dict[str, object]:
        """Представляет подписку как данные автора с рецептами.

        Args:
            instance: Сериализуемый экземпляр подписки.

        Returns:
            Сериализованные данные автора.
        """
        return UserWithRecipesSerializer(
            instance.author,
            context=self.context,
        ).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализует краткие данные рецепта для вложенных ответов."""

    class Meta:
        """Задает поля краткого представления рецепта."""

        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = fields


class UserWithRecipesSerializer(
    SubscriptionCheckMixin,
    serializers.ModelSerializer,
):
    """Сериализует профиль пользователя с краткими данными рецептов."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        """Задает поля пользователя."""

        model = UserModel
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )
        read_only_fields = fields

    def get_recipes(self, obj: User) -> list[dict[str, object]]:
        """Возвращает рецепты пользователя с учетом лимита из запроса.

        Args:
            obj: Пользователь, рецепты которого сериализуются.

        Returns:
            Сериализованные краткие данные рецептов.
        """
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()

        if limit:
            recipes = recipes[:int(limit)]
        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data

    def get_recipes_count(self, obj: User) -> int:
        """Возвращает количество рецептов, созданных пользователем.

        Args:
            obj: Пользователь, для которого запрашивается количество.

        Returns:
            Количество рецептов
        """
        if hasattr(obj, 'recipes_count'):
            return obj.recipes_count
        return obj.recipes.count()


class BaseUserItemRelationSerializer(serializers.ModelSerializer):
    """Сериализует связи рецепта с пользователем."""

    class Meta:
        """Задает базовые поля связи для дочерних сериализаторов."""

        fields = (
            'user',
            'recipe',
        )

    def validate(
        self,
        attrs: UserRecipeRelationData,
    ) -> UserRecipeRelationData:
        """Проверяет, что связь пользователя и рецепта еще не существует.

        Args:
            attrs: Входные данные связи с пользователем и рецептом.

        Returns:
            Проверенные данные связи.
        """
        user = attrs.get('user')
        recipe = attrs.get('recipe')
        model = self.Meta.model

        if model.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(
                f'Рецепт "{recipe.name}" уже добавлен.',
            )
        return attrs

    def to_representation(
        self,
        instance: Favorite | ShoppingCart,
    ) -> dict[str, object]:
        """Представляет сохраненную связь как краткие данные рецепта.

        Args:
            instance: Экземпляр связи, содержащий рецепт.

        Returns:
            Сериализованные краткие данные рецепта.
        """
        return RecipeShortSerializer(instance.recipe).data


class ShoppingCartSerializer(BaseUserItemRelationSerializer):
    """Сериализует добавление рецепта в список покупок."""

    class Meta(BaseUserItemRelationSerializer.Meta):
        """Задает модель связи со списком покупок."""

        model = ShoppingCart


class FavoriteSerializer(BaseUserItemRelationSerializer):
    """Сериализует добавление рецепта в избранное."""

    class Meta(BaseUserItemRelationSerializer.Meta):
        """Задает модель связи с избранным."""

        model = Favorite
