"""Модели пользователей, профилей и подписок."""

from django.contrib.auth.models import AbstractUser
from django.db import models

EMAIL_MAX_LENGTH = 254
NAME_MAX_LENGTH = 150


class User(AbstractUser):
    """Модель пользователя.

    Attributes:
        email: Уникальный адрес электронной почты пользователя.
        first_name: Имя пользователя.
        last_name: Фамилия пользователя.
        avatar: Изображение профиля пользователя.
    """

    email = models.EmailField(
        "Электронная почта",
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
    )
    first_name = models.CharField("Имя", max_length=NAME_MAX_LENGTH)
    last_name = models.CharField("Фамилия", max_length=NAME_MAX_LENGTH)
    avatar = models.ImageField(
        upload_to="users/avatars/",
        null=True,
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        """Задает метаданные модели пользователя."""

        verbose_name = "пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["id"]

    def __str__(self):
        """Возвращает имя пользователя."""
        return self.username


class UserProfile(models.Model):
    """Дополнительный профиль пользователя.

    Attributes:
        user: Пользователь, которому принадлежит профиль.
        avatar: Аватарка.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    avatar = models.ImageField(
        "Иконка пользователя",
        upload_to="avatars/",
        blank=True,
    )

    class Meta:
        """Задает метаданные модели профиля."""

        verbose_name = "профиль"
        verbose_name_plural = "Профили"
        ordering = ["id"]

    def __str__(self):
        """Возвращает строковое представление профиля."""
        return f"Профиль пользователя {self.user.username}"


class Follow(models.Model):
    """Подписка одного пользователя на другого.

    Attributes:
        user: Пользователь, который оформил подписку.
        author: Пользователь, на которого осуществляется подписка.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )

    class Meta:
        """Задает метаданные модели подписки."""

        verbose_name = "подписка"
        verbose_name_plural = "Подписки"
        ordering = ["author"]

        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="unique_user_author",
            ),
        ]

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return (
            f"Пользователь {self.user.username} подписан на "
            f"пользователя {self.author.username}"
        )
