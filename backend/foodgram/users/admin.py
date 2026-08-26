"""Настройки админки для моделей пользователей."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import Follow, User

admin.site.empty_value_display = '-пусто-'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админка для модели пользователя."""

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'get_avatar_preview',
        'is_active',
        'is_staff',
    )
    list_editable = ('is_active',)
    list_filter = ('is_active', 'is_staff')
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            'Дополнительно',
            {
                'fields': ('avatar',),
            },
        ),
    )

    @admin.display(description='Аватар')
    def get_avatar_preview(self, obj):
        """Возвращает превью аватара пользователя."""
        if obj.avatar:
            return format_html(
                '<img src="{}" width="80" height="80" '
                'style="object-fit: cover; border-radius: 50%;">',
                obj.avatar.url,
            )

        return 'Аватар не загружен'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Админка для управления подписками."""

    list_display = ('user', 'author')
    search_fields = (
        'user__username',
        'author__username',
    )
    list_select_related = ('user', 'author')
