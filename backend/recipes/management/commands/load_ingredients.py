from recipes.management.commands.base_import_command import BaseImportCommand
from recipes.models import Ingredient


class Command(BaseImportCommand):
    help = 'Загрузка ингредиентов из JSON файла'
    model = Ingredient
    default_file = 'data/ingredients.json'
