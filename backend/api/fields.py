import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Кастомное поле, декодирующее Base64-строку."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format_part, imgstr = data.split(';base64,')
            ext = format_part.split('/')[-1]

            try:
                decoded_file = base64.b64decode(imgstr)
            except TypeError:
                raise serializers.ValidationError(
                    'Некорректная Base64-строка изображения.'
                )
            file_uuid = uuid.uuid4()
            data = ContentFile(decoded_file, name=f'{file_uuid}.{ext}')

        return super().to_internal_value(data)
