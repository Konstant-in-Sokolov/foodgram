# recipes/fields.py
import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Кастомное поле, декодирующее Base64-строку в объект ContentFile."""

    def to_internal_value(self, data):
        # 1. Проверяем, что это Base64-строка (она начинается с 'data:image')
        if isinstance(data, str) and data.startswith('data:image'):
            # 2. Разделяем строку на тип файла и данные Base64
            format_part, imgstr = data.split(';base64,')
            ext = format_part.split('/')[-1]

            # 3. Декодируем Base64
            try:
                decoded_file = base64.b64decode(imgstr)
            except TypeError:
                raise serializers.ValidationError(
                    'Некорректная Base64-строка изображения.'
                )

            # 4. Создаем объект ContentFile с уникальным именем
            data = ContentFile(decoded_file, name=f'{uuid.uuid4()}.{ext}')

        # 5. Передаем ContentFile стандартному ImageField
        # для валидации и сохранения
        return super().to_internal_value(data)
