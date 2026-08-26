"""Настройки админки для моделей рецептов."""

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient, RecipeTag,
                     ShoppingCart, Tag)

admin.site.empty_value_display = '-пусто-'


class RecipeIngredientInline(admin.TabularInline):
    """Добавляет ингредиенты в карточку рецепта."""

    model = RecipeIngredient
    extra = 1
    min_num = 1
    validate_min = True


class RecipeTagInline(admin.TabularInline):
    """Добавляет теги в карточку рецепта."""

    model = RecipeTag
    extra = 1
    min_num = 1
    validate_min = True


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Панель управления рецептами."""

    inlines = (RecipeTagInline, RecipeIngredientInline)

    list_display = (
        'name',
        'author',
        'cooking_time',
        'get_tags',
        'get_image_preview',
        'get_favorites_count',
    )
    list_filter = ('author', 'tags__name')
    search_fields = ('name', 'author__username', 'tags__name')
    readonly_fields = ('get_favorites_count',)

    @admin.display(description='Текущее изображение')
    def get_image_preview(self, obj):
        """Превью изображения."""
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" '
                'style="object-fit: cover; border-radius: 8px;">',
                obj.image.url,
            )
        return 'Изображение не загружено'

    def get_queryset(self, request):
        """Добавляет количество добавлений в избранное."""
        return (
            super().get_queryset(request)
            .select_related('author')
            .prefetch_related('tags')
            .annotate(favorites_count=Count('in_favorites'))
        )

    @admin.display(description='Теги')
    def get_tags(self, obj):
        """Вывод списка тегов."""
        return ', '.join(tag.name for tag in obj.tags.all())

    @admin.display(
        description='В избранном',
        ordering='favorites_count',
    )
    def get_favorites_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorites_count


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Панель управления ингредиентами."""

    list_display = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    search_fields = ('name',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Панель управления ингредиентами рецептов."""

    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_select_related = ('recipe', 'ingredient')


@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    """Панель управления тегами рецептов."""

    list_display = ('recipe', 'tag')
    search_fields = ('recipe__name', 'tag__name')
    list_select_related = ('recipe', 'tag')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Панель управления тегами."""

    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Панель управления избранным."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_select_related = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Панель управления списком покупок."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_select_related = ('user', 'recipe')
