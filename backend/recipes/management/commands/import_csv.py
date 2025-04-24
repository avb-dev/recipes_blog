import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag

DATA_DIR = os.path.join(settings.BASE_DIR, "data")


class Command(BaseCommand):
    help = "Импортирует в базу данных данные из CSV-файлов"
    requires_migrations_checks = True
    MODEL_MAP = {
        "ingredients.csv": Ingredient,
        "tags.csv": Tag,
    }

    def handle(self, *args, **kwargs):
        if not os.path.exists(DATA_DIR):
            self.stderr.write(
                self.style.ERROR(f"Директория {DATA_DIR} не найдена"))
            return

        csv_files = [
            f for f in os.listdir(DATA_DIR) if f.endswith(".csv")
        ]

        if not csv_files:
            self.stdout.write(self.style.WARNING("Нет CSV файлов для импорта"))
            return

        self.import_csv("ingredients.csv")
        self.import_csv("tags.csv")

        self.stdout.write(self.style.SUCCESS(
            "Данные из CSV файлов успешно импортированы"))

    def import_csv(self, file_name):
        """
        Импортирует данные из CSV файла в соответствующую модель.

        Метод открывает CSV файл, читает данные и в зависимости от типа файла
        связывает их с нужными объектами, например, с категориями или
        пользователями.
        """

        model = self.MODEL_MAP.get(file_name)
        if not model:
            self.stderr.write(
                self.style.WARNING(f"Нет модели для {file_name}."))
            return

        file_path = os.path.join(DATA_DIR, file_name)

        try:
            with open(file_path, newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                data_to_insert = []

                for row in reader:
                    data_to_insert.append(model(**row))

                model.objects.bulk_create(data_to_insert,
                                          ignore_conflicts=True)
                self.stdout.write(self.style.SUCCESS(
                    f"Импортировано {len(data_to_insert)} "
                    f"записей из {file_name}"))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"Файл {file_name} не найден"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f"Ошибка при импорте данных из {file_name}: {str(e)}"))
