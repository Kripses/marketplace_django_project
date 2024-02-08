import pathlib

from django.conf import settings
from django.core.management import BaseCommand

from products.tasks import import_products


class Command(BaseCommand):
    help = "Import products data, adding it to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            '-f',
            '--file',
            required=False,
            nargs='+',
            help='Specify a zip-archive file to product_import',
        )
        parser.add_argument(
            '-e',
            '--email',
            required=False,
            nargs='?',
            help='Specify an admin email to send a notification',
        )

    def handle(self, *args, **options):
        self.stdout.write('Begin product product_import')

        files = options.get('file')
        pending_imports_dir = settings.IMPORT_PENDING_DIR

        if files:
            files = [pending_imports_dir.joinpath(f)
                     for f in files if f.endswith('.zip')]
        else:

            try:
                files = [f for f in pathlib.Path(pending_imports_dir).iterdir()
                         if f.is_file()]
            except FileNotFoundError:
                self.stdout.write(
                    self.style.ERROR('Import category doesn\'t exist')
                )
                return

        email = options.get('email')

        if files:
            for file in files:
                import_products.delay(file.as_posix(), email)
            self.stdout.write(f'{len(files)} file(s) added to product_import query')
        else:
            self.stdout.write(self.style.WARNING('No files to product_import'))
