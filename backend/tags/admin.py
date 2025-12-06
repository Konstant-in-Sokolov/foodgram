from django.contrib import admin

from .models import Tag


class TagAdmin(admin.ModelAdmin):
    # Автоматическое заполнение слага из имени
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


admin.site.register(Tag, TagAdmin)
