from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.core.management.commands.safe_migrate import Command as SafeMigrationCommand


class MigrationGuardTests(TestCase):
    def test_current_history_is_read_only_and_known(self):
        output = StringIO()
        with CaptureQueriesContext(connection) as queries:
            call_command('check_database_compatibility', stdout=output)
        self.assertIn('known and consistent', output.getvalue())
        for query in queries:
            statement = query['sql'].strip().upper()
            self.assertFalse(statement.startswith(('INSERT ', 'UPDATE ', 'DELETE ', 'CREATE ', 'ALTER ', 'DROP ')))

    def test_newer_migration_record_blocks_downgrade(self):
        MigrationRecorder(connection).record_applied('wagtailcore', '9999_future_release_fixture')
        with self.assertRaisesMessage(CommandError, 'absent from this release'):
            call_command('check_database_compatibility', stdout=StringIO())

    def test_require_empty_rejects_existing_database(self):
        with self.assertRaisesMessage(CommandError, 'empty test database'):
            call_command('check_database_compatibility', require_empty=True, stdout=StringIO())

    def test_safe_migrate_never_reaches_migrate_after_a_failed_guard(self):
        with patch('apps.core.management.commands.safe_migrate.call_command', side_effect=CommandError('blocked')) as invoke:
            with self.assertRaises(CommandError):
                SafeMigrationCommand().handle(database='default', interactive=False, verbosity=0)
        self.assertEqual(invoke.call_count, 1)
        self.assertEqual(invoke.call_args.args[0], 'check_database_compatibility')

    def test_safe_migrate_checks_models_before_writing(self):
        with patch('apps.core.management.commands.safe_migrate.call_command') as invoke:
            SafeMigrationCommand().handle(database='default', interactive=False, verbosity=0)
        self.assertEqual([item.args[0] for item in invoke.call_args_list],
                         ['check_database_compatibility', 'makemigrations', 'migrate'])
        self.assertTrue(invoke.call_args_list[1].kwargs['check'])
        self.assertTrue(invoke.call_args_list[1].kwargs['dry_run'])
