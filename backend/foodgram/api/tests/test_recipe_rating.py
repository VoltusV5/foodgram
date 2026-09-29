"""Проверки API оценок рецептов."""

from recipes.models import Recipe, RecipeRating
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User


class RecipeRatingAPITest(APITestCase):
    """Проверяет создание, изменение и управление оценками."""

    def setUp(self) -> None:
        self.author = User.objects.create_user(
            email="author@example.com",
            username="author",
            first_name="Автор",
            last_name="Рецепта",
            password="strong-password",
        )
        self.user = User.objects.create_user(
            email="user@example.com",
            username="user",
            first_name="Пользователь",
            last_name="Теста",
            password="strong-password",
        )
        self.recipe = Recipe.objects.create(
            author=self.author,
            name="Тестовый рецепт",
            text="Описание тестового рецепта.",
            cooking_time=15,
        )
        self.url = f"/api/recipes/{self.recipe.id}/rating/"

    def test_authenticated_user_can_create_and_change_rating(self) -> None:
        """Повторная оценка изменяет голос, не создавая новый."""
        self.client.force_authenticate(self.user)

        response = self.client.put(self.url, {"value": 5}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rating"], 5.0)
        self.assertEqual(response.data["ratings_count"], 1)
        self.assertEqual(response.data["user_rating"], 5)

        response = self.client.put(self.url, {"value": 3}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(RecipeRating.objects.count(), 1)
        self.assertEqual(RecipeRating.objects.get().value, 3)
        self.assertEqual(response.data["rating"], 3.0)

    def test_rating_aggregates_votes_of_different_users(self) -> None:
        """Ответ содержит среднее значение и количество голосов."""
        self.client.force_authenticate(self.user)
        self.client.put(self.url, {"value": 3}, format="json")

        second_user = User.objects.create_user(
            email="second@example.com",
            username="second",
            first_name="Второй",
            last_name="Пользователь",
            password="strong-password",
        )
        self.client.force_authenticate(second_user)
        response = self.client.put(self.url, {"value": 5}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rating"], 4.0)
        self.assertEqual(response.data["ratings_count"], 2)
        self.assertEqual(response.data["user_rating"], 5)

    def test_rating_requires_authentication_and_valid_value(self) -> None:
        """Голосовать могут только авторизованные пользователи."""
        response = self.client.put(self.url, {"value": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, {"value": 6}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(RecipeRating.objects.count(), 0)
