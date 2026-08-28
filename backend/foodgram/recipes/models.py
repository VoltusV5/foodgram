"""Модели рецептов, ингредиентов, тегов и связей."""

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """Тег для классификации рецептов.

    Attributes:
        name: Уникальное название тега.
        slug: Уникальный URL-идентификатор тега.
    """

    name = models.CharField("Название тега", max_length=50, unique=True)
    slug = models.SlugField("Слаг тега", max_length=150, unique=True)

    class Meta:
        """Задает метаданные модели тега."""

        verbose_name = "тег"
        verbose_name_plural = "Теги"
        ordering = ["name"]

    def __str__(self):
        """Возвращает название тега."""
        return self.name


class Ingredient(models.Model):
    """Ингредиент и ед. измерения.

    Attributes:
        name: Название ингредиента.
        measurement_unit: Единица измерения ингредиента (граммы, литры и т.д.).
    """

    name = models.CharField(
        "Название ингредиента",
        max_length=128,
    )
    measurement_unit = models.CharField(
        "Единица измерения",
        max_length=50,
        default="г",
    )

    class Meta:
        """Задает метаданные модели ингредиента."""

        verbose_name = "ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient_unit",
            ),
        ]

    def __str__(self):
        """Возвращает представление ингредиента."""
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    """Рецепт пользователя.

    Attributes:
        name: Название рецепта.
        author: Пользователь, создавший рецепт.
        image: Изображение рецепта.
        text: Описание рецепта.
        ingredients: Ингредиенты, входящие в рецепт.
        tags: Теги рецепта.
        cooking_time: Время приготовления в минутах.
    """

    name = models.CharField("Название рецепта", max_length=256)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор рецепта",
    )
    image = models.ImageField(
        "Изображение рецепта",
        upload_to="recipes_icons/",
        blank=True,
    )
    text = models.TextField("Описание")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ингредиенты",
    )
    tags = models.ManyToManyField(
        Tag,
        through="RecipeTag",
        related_name="recipes",
        verbose_name="Теги",
    )
    cooking_time = models.PositiveIntegerField(
        "Время приготовления в минутах",
        validators=[
            MinValueValidator(
                1,
                message="Время приготовления должно быть >= 1 минуты",
            ),
        ],
    )

    class Meta:
        """Задает метаданные модели рецепта."""

        verbose_name = "рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-id"]

    def __str__(self):
        """Возвращает название рецепта."""
        return self.name


class RecipeIngredient(models.Model):
    """Связывает рецепт с ингредиентом и указывает его количество.

    Attributes:
        recipe: Рецепт, в который добавлен ингредиент.
        ingredient: Добавленный ингредиент.
        amount: Количество ингредиента.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredient_recipes",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveIntegerField(
        "Количество",
        default=1,
        validators=[
            MinValueValidator(1, message="Количество должно быть >= 1"),
        ],
    )

    class Meta:
        """Задает метаданные связи рецепта с ингредиентом."""

        verbose_name = "ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            ),
        ]

    def __str__(self):
        """Возвращает представление ингредиента в рецепте."""
        return f"{self.ingredient.name} в рецепте «{self.recipe.name}»"


class RecipeTag(models.Model):
    """Связывает рецепт с тегом.

    Attributes:
        recipe: Рецепт, которому назначен тег.
        tag: Назначенный тег.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_tags",
        verbose_name="Рецепт",
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="recipe_tags",
        verbose_name="Тег",
    )

    class Meta:
        """Задает метаданные связи рецепта с тегом."""

        verbose_name = "тег рецепта"
        verbose_name_plural = "Теги рецептов"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "tag"],
                name="unique_recipe_tag",
            ),
        ]

    def __str__(self):
        """Возвращает представление тега рецепта."""
        return f"Рецепт {self.recipe.name} с тегом {self.tag.name}"


class UserRecipeRelation(models.Model):
    """Связь между пользователем и рецептом.

    Пара user и recipe должна быть уникальной.
    """

    class Meta:
        """Задает общие метаданные абстрактной связи."""

        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_%(app_label)s_%(class)s",
            ),
        ]

    def __str__(self):
        """Возвращает идентификаторы пользователя и рецепта."""
        return f"{self.user_id} --- {self.recipe_id}"


class Favorite(UserRecipeRelation):
    """Рецепт, добавленный пользователем в избранное.

    Attributes:
        user: Пользователь, добавивший рецепт в избранное.
        recipe: Добавленный в избранное рецепт.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_favorites",
        verbose_name="Рецепт",
    )

    class Meta(UserRecipeRelation.Meta):
        """Задает метаданные модели избранного."""

        verbose_name = "избранное"
        verbose_name_plural = "Избранное"


class ShoppingCart(UserRecipeRelation):
    """Рецепт, добавленный пользователем в список покупок.

    Attributes:
        user: Пользователь, добавивший рецепт в список покупок.
        recipe: Добавленный в список покупок рецепт.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_shopping_carts",
        verbose_name="Рецепт",
    )

    class Meta(UserRecipeRelation.Meta):
        """Задает метаданные модели списка покупок."""

        verbose_name = "список покупок"
        verbose_name_plural = "Списки покупок"
