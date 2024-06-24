import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Delete specified files'

    def add_arguments(self, parser):
        parser.add_argument('file_paths', nargs='+', type=str)

    def handle(self, *args, **kwargs):
        file_paths = kwargs['file_paths']
        for file_path in file_paths:
            try:
                os.remove(file_path)
                self.stdout.write(self.style.SUCCESS(f'Successfully deleted {file_path}'))
            except OSError as e:
                self.stdout.write(self.style.ERROR(f'Error deleting {file_path}: {e}'))
