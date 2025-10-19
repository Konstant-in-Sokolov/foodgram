from django.db import models


class Tags(models.Model):
    """Модель для тегов."""

    name = models.CharField(
        'Имя_Тега',
        max_length=20,
        unique=True
    )
    slug = models.SlugField(
        'Слаг',
        max_length=20,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name
