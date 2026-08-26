"""Сериализаторы рецептов, ингредиентов и тегов."""

from typing import TypedDict

from api.v1.serializers.fields import Base64ImageField
from api.v1.serializers.users import CustomUserSerializer
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from rest_framework import serializers


class RecipeIngredientData(TypedDict):
    """Описывает проверенные данные ингредиента в рецепте."""

    ingredient: Ingredient
    amount: int


class TagSerializer(serializers.ModelSerializer):
    """Сериализует данные тега рецепта."""

    class Meta:
        """Задает поля сериализатора тега."""

        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализует данные ингредиента."""

    class Meta:
        """Задает поля сериализатора ингредиента."""

        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализует данные ингредиента в рецепте для чтения."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        """Задает поля ингредиента рецепта, возвращаемые в ответе."""

        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализует данные ингредиента в рецепте для записи."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        """Задает поля ингредиента рецепта, принимаемые в запросе."""

        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализует данные рецепта для ответов на запросы чтения."""

    author = CustomUserSerializer()
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True,
        source='recipe_ingredients',
    )
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)
    image = Base64ImageField()

    class Meta:
        """Задает поля рецепта."""

        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = fields


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализует данные рецепта для создания и обновления."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        """Задает поля рецепта, принимаемые эндпоинтами записи."""

        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, data: dict[str, object]) -> dict[str, object]:
        """Проверяет обязательность и уникальность ингредиентов и тегов.

        Args:
            data: Входные данные рецепта.

        Returns:
            Проверенные данные рецепта.
        """
        ingredients = data.get('ingredients')
        tags = data.get('tags')

        if not ingredients:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.',
            )
        if not tags:
            raise serializers.ValidationError(
                'Укажите хотя бы один тег.',
            )

        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.',
            )

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.',
            )

        return data

    def _create_ingredients(
        self,
        recipe: Recipe,
        ingredients_data: list[RecipeIngredientData],
    ) -> None:
        """Создает связи ингредиентов с рецептом массовой вставкой.

        Args:
            recipe: Рецепт, к которому привязываются ингредиенты.
            ingredients_data: Данные связей с ингредиентами.
        """
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount'],
            ) for item in ingredients_data
        ])

    def create(self, validated_data: dict[str, object]) -> Recipe:
        """Создает рецепт с тегами и ингредиентами.

        Args:
            validated_data: Проверенные данные рецепта.

        Returns:
            Созданный экземпляр рецепта.
        """
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._create_ingredients(recipe, ingredients)
        return recipe

    def update(
        self,
        instance: Recipe,
        validated_data: dict[str, object],
    ) -> Recipe:
        """Обновляет рецепт и заменяет переданные теги или ингредиенты.

        Args:
            instance: Экземпляр рецепта для обновления.
            validated_data: Проверенные данные рецепта.

        Returns:
            Обновленный экземпляр рецепта.
        """
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            self._create_ingredients(instance, ingredients)

        return super().update(instance, validated_data)

    def to_representation(self, instance: Recipe) -> dict[str, object]:
        """Представляет записанный рецепт в формате сериализатора чтения.

        Args:
            instance: Экземпляр рецепта для сериализации.

        Returns:
            Сериализованные данные рецепта для ответа API.
        """
        return RecipeReadSerializer(instance, context=self.context).data
