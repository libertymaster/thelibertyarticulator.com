"""Single-owner forward migration entry point; no automatic reversal or fake mode."""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Check framework/history/model state, then apply normal forward migrations.'

    def add_arguments(self, parser):
        parser.add_argument('--noinput', '--no-input', action='store_false', dest='interactive', default=True)
        parser.add_argument('--database', default='default')

    def handle(self, *args, **options):
        call_command('check_database_compatibility', database=options['database'], verbosity=options['verbosity'])
        # Never generate or apply an unreviewed model migration during deployment.
        call_command('makemigrations', check=True, dry_run=True, verbosity=options['verbosity'])
        call_command('migrate', database=options['database'], interactive=options['interactive'],
                     verbosity=options['verbosity'])
