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

        try:
            with open(file_path, 'r', encoding='utf-8') as f:

                created_count = len(self.model.objects.bulk_create(
                    (self.model(**item) for item in json.load(f)),
                    ignore_conflicts=True
                ))

            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(
                self.style.SUCCESS(
                    f'{self.object_name.upper()} ИМПОРТИРОВАНЫ:'
                )
            )
            self.stdout.write(f'Создано новых записей: {created_count}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка при загрузке {self.object_name} '
                    f'из {file_path}: {e}'
                )
            )
