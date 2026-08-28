"""Команда для заполнения базы тестовыми данными."""

import json
import os
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import connection, transaction
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Follow, User

DATA_DIR = settings.BASE_DIR.parent.parent / "data"
TEST_DATA_FILE = DATA_DIR / "test_data.json"
INGREDIENTS_FILE = DATA_DIR / "ingredients.json"
IMAGES_DIR = DATA_DIR / "recipe_images"

REQUIRED_ENV_VARIABLES = (
    "ADMIN_EMAIL",
    "ADMIN_USERNAME",
    "ADMIN_PASSWORD",
    "TEST_USER_PASSWORD",
)


class Command(BaseCommand):
    """Создает тестовых пользователей, рецепты и связи."""

    def handle(self, *args: object, **options: object) -> None:
        """Создает тестовые данные, очищая БД при запросе."""
        should_clear_database = self._should_clear_database()
        test_data = self._load_json(TEST_DATA_FILE)
        ingredients_data = self._load_json(INGREDIENTS_FILE)

        self._validate_environment()

        with transaction.atomic():
            if should_clear_database:
                self._clear_database()

            self._create_tags(test_data["tags"])
            self._create_ingredients(ingredients_data)
            users = self._create_users(test_data["users"])
            recipes = self._create_recipes(users, test_data["recipes"])
            self._create_relations(
                users,
                recipes,
                test_data["relations"],
            )

    def _should_clear_database(self) -> bool:
        """Запрашивает подтверждение очистки данных."""
        answer = (
            input(
                "Очистить данные пользователей, рецептов и ингредиентов? [y/N]: ",
            )
            .strip()
            .lower()
        )
        return answer == "y"

    def _clear_database(self) -> None:
        """Удаляет пользователей, рецепты, ингредиенты и теги."""
        User.objects.all().delete()
        Ingredient.objects.all().delete()
        Tag.objects.all().delete()

        sequences = [
            {"table": model._meta.db_table, "column": model._meta.pk.column}
            for model in (
                *apps.get_app_config("users").get_models(),
                *apps.get_app_config("recipes").get_models(),
            )
        ]
        reset_queries = connection.ops.sequence_reset_by_name_sql(
            no_style(),
            sequences,
        )
        with connection.cursor() as cursor:
            for query in reset_queries:
                cursor.execute(query)

    def _load_json(self, file_path: Path):
        """Читает данные из JSON-файла."""
        if not file_path.is_file():
            raise CommandError(f'Файл "{file_path}" не найден.')

        try:
            with file_path.open(encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as error:
            raise CommandError(f'Некорректный JSON "{file_path}"') from error

    def _validate_environment(self) -> None:
        """Проверяет обязательные переменные окружения."""
        missing_variables = [
            name for name in REQUIRED_ENV_VARIABLES if not os.getenv(name)
        ]
        if missing_variables:
            raise CommandError(
                "Не заданы переменные окружения: " f'{", ".join(missing_variables)}.',
            )

    def _create_tags(self, tags_data: list[dict]) -> None:
        """Создает или обновляет теги."""
        for tag_data in tags_data:
            Tag.objects.update_or_create(
                slug=tag_data["slug"],
                defaults={"name": tag_data["name"]},
            )

    def _create_ingredients(self, ingredients_data: list[dict]) -> None:
        """Импортирует отсутствующие ингредиенты."""
        ingredient_keys = {
            (item["name"].strip(), item["measurement_unit"].strip())
            for item in ingredients_data
            if item.get("name") and item.get("measurement_unit")
        }
        Ingredient.objects.bulk_create(
            [
                Ingredient(name=name, measurement_unit=unit)
                for name, unit in ingredient_keys
            ],
            ignore_conflicts=True,
        )

    def _create_users(self, users_data: list[dict]) -> dict[str, User]:
        """Создает администратора и тестовых пользователей."""
        admin, created = User.objects.get_or_create(
            username=os.environ["ADMIN_USERNAME"],
            defaults={
                "email": os.environ["ADMIN_EMAIL"],
                "first_name": os.getenv("ADMIN_FIRST_NAME", "Admin"),
                "last_name": os.getenv("ADMIN_LAST_NAME", ""),
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created or not admin.has_usable_password():
            admin.set_password(os.environ["ADMIN_PASSWORD"])
            admin.save(update_fields=("password",))

        users = {}
        for user_data in users_data:
            user, created = User.objects.update_or_create(
                username=user_data["username"],
                defaults={
                    "email": user_data["email"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                },
            )
            if created:
                user.set_password(os.environ["TEST_USER_PASSWORD"])
                user.save(update_fields=("password",))
            users[user.username] = user
        return users

    def _create_recipes(
        self,
        users: dict[str, User],
        recipes_data: list[dict],
    ) -> dict[str, Recipe]:
        """Создает рецепты с тегами, ингредиентами и изображениями."""
        ingredient_names = {
            ingredient["name"]
            for recipe in recipes_data
            for ingredient in recipe["ingredients"]
        }
        ingredient_map = {
            (ingredient.name, ingredient.measurement_unit): ingredient
            for ingredient in Ingredient.objects.filter(
                name__in=ingredient_names,
            )
        }
        tag_map = Tag.objects.in_bulk(field_name="slug")
        recipes = {}

        for recipe_data in recipes_data:
            recipe, _ = Recipe.objects.update_or_create(
                name=recipe_data["name"],
                author=users[recipe_data["author"]],
                defaults={
                    "text": recipe_data["text"],
                    "cooking_time": recipe_data["cooking_time"],
                },
            )
            recipe.tags.set(tag_map[slug] for slug in recipe_data["tags"])
            recipe.recipe_ingredients.all().delete()

            try:
                RecipeIngredient.objects.bulk_create(
                    [
                        RecipeIngredient(
                            recipe=recipe,
                            ingredient=ingredient_map[
                                item["name"],
                                item["measurement_unit"],
                            ],
                            amount=item["amount"],
                        )
                        for item in recipe_data["ingredients"]
                    ]
                )
            except KeyError as error:
                raise CommandError(
                    f"Ингредиент рецепта не найден: {error}.",
                ) from error

            if not recipe.image:
                image_name = recipe_data["image"]
                with (IMAGES_DIR / image_name).open("rb") as image:
                    recipe.image.save(image_name, File(image), save=True)

            recipes[recipe_data["key"]] = recipe
        return recipes

    def _create_relations(
        self,
        users: dict[str, User],
        recipes: dict[str, Recipe],
        relations: dict,
    ) -> None:
        """Создает подписки, избранное и списки покупок."""
        for relation in relations["follows"]:
            Follow.objects.get_or_create(
                user=users[relation["user"]],
                author=users[relation["author"]],
            )
        for relation in relations["favorites"]:
            Favorite.objects.get_or_create(
                user=users[relation["user"]],
                recipe=recipes[relation["recipe"]],
            )
        for relation in relations["shopping_cart"]:
            ShoppingCart.objects.get_or_create(
                user=users[relation["user"]],
                recipe=recipes[relation["recipe"]],
            )
