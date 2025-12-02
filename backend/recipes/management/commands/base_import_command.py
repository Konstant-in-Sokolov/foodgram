import json

from django.core.management.base import BaseCommand


class BaseImportCommand(BaseCommand):
    model = None
    default_file = ''

    @property
    def object_name(self):
        return self.model._meta.verbose_name_plural

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default=self.default_file,
            help=f'Путь к JSON-файлу с {self.object_name}.',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        name_upper = self.object_name.upper()

        try:
            with open(file_path, 'r', encoding='utf-8') as file:

                created_count = len(self.model.objects.bulk_create(
                    (self.model(**item) for item in json.load(file)),
                    ignore_conflicts=True
                ))

        except Exception as error:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка при загрузке {self.object_name} '
                    f'из {file_path}: {error}'
                )
            )
            return

        self.stdout.write(f'\n{'=' * 50}')
        self.stdout.write(
            self.style.SUCCESS(
                f'{name_upper} ИМПОРТИРОВАНЫ: '
            )
        )
        self.stdout.write(f'Создано новых записей: {created_count}')
