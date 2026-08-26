"""Поле сериализатора для обработки изображений в Base64."""

import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Преобразует изображения в формате Base64 в файлы изображений."""

    def to_internal_value(self, data):
        """Преобразует Base64 в изображение."""
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format_header, base64_data = data.split(';base64,')
                ext = format_header.split('/')[-1]

                file_name = f'{uuid.uuid4().hex[:10]}.{ext}'

                data = ContentFile(
                    base64.b64decode(base64_data), name=file_name,
                )

            except (ValueError, TypeError, base64.binascii.Error):
                raise serializers.ValidationError(
                    'Некорректный формат Base64-изображения.',
                )

        return super().to_internal_value(data)
