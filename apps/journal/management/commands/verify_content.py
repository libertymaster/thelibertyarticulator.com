from django.core.management.base import BaseCommand, CommandError
from apps.journal.models import ArticlePage, ChronologyPage

class Command(BaseCommand):
    help = 'Validate article reference integrity and chronology keys.'
    def handle(self, *args, **options):
        errors = []
        for page in list(ArticlePage.objects.all()) + list(ChronologyPage.objects.all()):
            try:
                page.clean()
            except Exception as exc:
                errors.append(f'{page.pk}: {exc}')
        if errors:
            raise CommandError('\n'.join(errors))
        self.stdout.write('Content references and chronology keys validated.')
