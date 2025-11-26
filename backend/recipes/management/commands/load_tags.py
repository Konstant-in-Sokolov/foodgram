from recipes.management.commands.base_import_command import BaseImportCommand
from recipes.models import Tag


class Command(BaseImportCommand):
    help = 'Загрузка тегов из JSON файла'
    model = Tag
    default_file = 'data/tags.json'
