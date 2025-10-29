import csv
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from ingredients.models import Ingredient


class Command(BaseCommand):
    help = 'Loads ingredients from the ingredients.csv'
    'file located in the data/ directory.'

    def handle(self, *args, **options):
        # Очищаем модель Ingredient перед загрузкой (опционально)
        Ingredient.objects.all().delete()
        self.stdout.write(self.style.WARNING('Existing ingredients cleared.'))

        # Указываем путь к вашему файлу ingredients.csv
        # Путь относительно корня проекта (backend/data/ingredients.csv)
        file_path = '../data/ingredients.csv'

        try:
            with open(file_path, encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                # Пропускаем заголовок, если он есть
                # next(reader)

                ingredients_to_create = []
                for row in reader:
                    # В CSV ожидаем 2 столбца: [название, единица_измерения]
                    if len(row) < 2:
                        self.stdout.write(
                            self.style.ERROR(f'Skipping invalid row: {row}')
                        )
                        continue

                    name = row[0].strip()
                    unit = row[1].strip()

                    ingredients_to_create.append(
                        Ingredient(name=name, measurement_unit=unit)
                    )

                # Создаем все объекты одним запросом (эффективно)
                Ingredient.objects.bulk_create(ingredients_to_create)

                self.stdout.write(self.style.SUCCESS(
                    f'Successfully loaded {len(ingredients_to_create)} ingredients.'
                ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                f'File not found: {file_path}.'
                'Make sure the file is in the correct location.'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
