"""ViewSet'ы API для рецептов."""

from django.db.models import Exists, F, OuterRef, QuerySet, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)

from ...permissions import IsAuthorOrAdminOrReadOnly
from ..filters import IngredientFilter, RecipeFilter
from ..pagination import CustomPagination
from ..serializers.mixins import BaseRelationMixin
from ..serializers.recipes import (IngredientSerializer, RecipeReadSerializer,
                                   RecipeWriteSerializer, TagSerializer)
from ..serializers.users import FavoriteSerializer, ShoppingCartSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Предоставляет доступ только для чтения к списку тегов."""

    queryset = Tag.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Предоставляет доступ только для чтения к списку ингредиентов."""

    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(BaseRelationMixin, viewsets.ModelViewSet):
    """Управляет рецептами и связанными с ними пользовательскими списками."""

    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self) -> QuerySet[Recipe]:
        """Возвращает рецепты с данными, необходимыми для сериализации.

        Returns:
            Дополненный набор рецептов.
        """
        user = self.request.user
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags',
            'recipe_ingredients__ingredient',
        )

        if user.is_anonymous:
            return queryset

        return queryset.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    user=user,
                    recipe=OuterRef('pk'),
                ),
            ),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user=user,
                    recipe=OuterRef('pk'),
                ),
            ),
        )

    def get_serializer_class(
        self,
    ) -> type[RecipeReadSerializer] | type[RecipeWriteSerializer]:
        """Выбирает сериализатор в зависимости от HTTP-метода.

        Returns:
            Класс сериализатора для текущего запроса.
        """
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer: RecipeWriteSerializer) -> None:
        """Сохраняет рецепт с текущим пользователем в качестве автора.

        Args:
            serializer: Валидный сериализатор создаваемого рецепта.
        """
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='get-link',
    )
    def get_link(self, request: Request, pk: str | None = None) -> Response:
        """Возвращает короткую ссылку на рецепт.

        Args:
            request: Входящий HTTP-запрос.
            pk: Первичный ключ рецепта из маршрута.

        Returns:
            Ответ с короткой ссылкой.
        """
        recipe = self.get_object()
        short_url = reverse('short-url', kwargs={'pk': recipe.pk})

        full_short_url = request.build_absolute_uri(short_url)
        return Response(
            {'short-link': full_short_url}, status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(
        self,
        request: Request,
        pk: str | None = None,
    ) -> Response:
        """Добавляет рецепт в список покупок или удаляет его.

        Args:
            request: Входящий HTTP-запрос.
            pk: Первичный ключ рецепта из маршрута.

        Returns:
            Ответ с рецептом или статусом удаления.
        """
        return self._manage_relation(
            ShoppingCart, ShoppingCartSerializer)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request: Request, pk: str | None = None) -> Response:
        """Добавляет рецепт в избранное или удаляет его.

        Args:
            request: Входящий HTTP-запрос.
            pk: Первичный ключ рецепта из маршрута.

        Returns:
            Ответ с рецептом или статусом удаления.
        """
        return self._manage_relation(
            Favorite, FavoriteSerializer)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request: Request) -> HttpResponse:
        """Формирует текстовый файл с ингредиентами из списка покупок.

        Args:
            request: Входящий HTTP-запрос.

        Returns:
            Текстовый файл со списком ингредиентов или сообщение об ошибке.
        """
        user = request.user

        aggregated_recipes = (
            RecipeIngredient.objects.filter(
                recipe__in_shopping_carts__user=user,
            )
            .values(
                name=F('ingredient__name'),
                unit=F('ingredient__measurement_unit'),
            )
            .annotate(total_amount=Sum('amount'))
            .order_by('name')
        )

        if not aggregated_recipes.exists():
            return HttpResponse(
                'Ваша корзина пуста.',
                status=status.HTTP_400_BAD_REQUEST,
                content_type='text/plain; charset=utf-8',
            )

        lines = ['Список ингредиентов:\n']
        for item in aggregated_recipes:
            lines.append(
                f"- {item['name']} ({item['unit']}) — {item['total_amount']}")

        content = '\n'.join(lines)

        response = HttpResponse(
            content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )
        return response


def redirect_to_recipe(
    request: Request,
    pk: int,
) -> HttpResponseRedirect:
    """Перенаправляет с короткой ссылки на страницу рецепта.

    Args:
        request: Входящий HTTP-запрос.
        pk: Первичный ключ рецепта.

    Returns:
        Перенаправление на страницу рецепта.
    """
    recipe = get_object_or_404(Recipe, pk=pk)
    return redirect(f'/recipes/{recipe.pk}/')
