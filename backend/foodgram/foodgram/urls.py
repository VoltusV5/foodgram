"""Конфигурация URL-маршрутов."""

from api.v1.views.recipes import redirect_to_recipe
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("s/<int:pk>/", redirect_to_recipe, name="short-url"),
    path(
        "recipes/<int:pk>/",
        TemplateView.as_view(template_name="index.html"),
        name="recipe-detail",
    ),
    path("api/", include("api.urls")),
    path(
        "api/docs/",
        TemplateView.as_view(template_name="redoc.html"),
        name="redoc",
    ),
    path(
        "api/docs/openapi-schema.yml",
        serve,
        {"document_root": settings.DOCS_DIR, "path": "openapi-schema.yml"},
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
