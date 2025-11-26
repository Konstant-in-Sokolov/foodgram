from django.contrib import admin

from .models import Tag


class TagAdmin(admin.ModelAdmin):
    # Автоматическое заполнение слага из имени
    prepopulated_fields = {'slug': ('name',)}
    # Отображаемые поля в списке
    list_display = ('name', 'slug')
    # Поля для поиска
    search_fields = ('name', 'slug')


admin.site.register(Tag, TagAdmin)
