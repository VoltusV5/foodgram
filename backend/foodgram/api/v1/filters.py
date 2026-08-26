"""Фильтры API для рецептов и ингредиентов."""

import django_filters
from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from recipes.models import Ingredient, Recipe, Tag

UserModel = get_user_model()


class RecipeFilter(django_filters.FilterSet):
    """Кастомный фильтр для рецептов."""

    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    author = django_filters.ModelChoiceFilter(
        queryset=UserModel.objects.all(),
    )

    is_favorited = django_filters.NumberFilter(
        method='filter_user_relation',
    )

    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_user_relation',
    )

    class Meta:
        """Задает модель и поля, доступные для фильтрации."""

        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_user_relation(
            self,
            queryset: QuerySet[Recipe],
            name: str,
            value: int,
    ) -> QuerySet[Recipe]:
        """Фильтрует рецепты для корзины и избранного.

        Args:
            queryset: Набор рецептов для фильтрации.
            name: Имя параметра фильтра.
            value: Значение параметра фильтра.

        Returns:
            Набор рецептов с учетом пользовательской связи.
        """
        user = self.request.user
        if not value or user.is_anonymous:
            return queryset

        relation = {
            'is_favorited': 'in_favorites__user',
            'is_in_shopping_cart': 'in_shopping_carts__user',
        }

        return queryset.filter(**{relation[name]: user})


class IngredientFilter(django_filters.FilterSet):
    """Фильтрация ингредиентов по началу названия."""

    name = django_filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        """Задает модель и поля, доступные для фильтрации."""

        model = Ingredient
        fields = ('name',)
