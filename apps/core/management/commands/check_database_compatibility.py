"""Read-only migration-history check; not a certification of a database downgrade."""
import importlib.metadata
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.migrations.loader import MigrationLoader

from apps.core.migration_history import unknown_migrations


class Command(BaseCommand):
    help = 'Reject foreign/newer migration history before migrating this exact baseline. Does not write data.'

    def add_arguments(self, parser):
        parser.add_argument('--database', default='default')
        parser.add_argument('--require-empty', action='store_true', help='Also refuse any existing application tables.')

    def handle(self, *args, **options):
        baseline = json.loads((Path(settings.BASE_DIR) / 'config/build-baseline.json').read_text())
        for package, expected in baseline['packages'].items():
            if importlib.metadata.version(package) != expected:
                raise CommandError('Installed framework differs from the approved baseline: ' + package)
        connection = connections[options['database']]
        # Introspection and MigrationLoader only read schema/history here.
        tables = set(connection.introspection.table_names())
        if options['require_empty'] and tables:
            raise CommandError('Expected an empty test database. Preserve existing volumes; choose a new project/database.')
        if 'django_migrations' not in tables:
            if tables:
                raise CommandError('Database has tables but no Django migration history. Refusing automatic initialization.')
            self.stdout.write('Empty database. This check did not create tables.')
            return
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        replaced = {key: migration.replaces for key, migration in loader.disk_migrations.items() if migration.replaces}
        unknown = unknown_migrations(loader.applied_migrations, loader.disk_migrations, replaced)
        if unknown:
            names = ', '.join(f'{app}.{name}' for app, name in unknown[:12])
            raise CommandError(
                'Migration history contains entries absent from this release: ' + names + '. '
                'Do not delete history, use --fake, or remove volumes. Test a compatible restored backup '
                'or a reviewed content migration into a fresh database.'
            )
        loader.check_consistent_history(connection)
        self.stdout.write('Migration history is known and consistent. This does not certify schema/data '
                          'compatibility or make a Wagtail 8 database downgrade safe.')
