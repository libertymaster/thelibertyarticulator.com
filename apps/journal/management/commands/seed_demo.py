from datetime import date
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.journal.models import (HomePage, ArticlePage, ArticleAuthor, ArticleSource, Subject, Series,
                                 ChronologyPage, ChronologyEvent)

class Command(BaseCommand):
    help = "Create clearly fictional demonstration content. Draft by default."
    def add_arguments(self, parser):
        parser.add_argument('--publish-demo', action='store_true', help='Explicitly publish fictional examples. Development only.')
    @transaction.atomic
    def handle(self, *args, **options):
        from django.conf import settings
        if options['publish_demo'] and not settings.DEBUG and not getattr(settings, 'ALLOW_TEST_DEMO', False):
            raise CommandError('Public demo publishing is disabled outside development/test settings.')
        home = HomePage.objects.first()
        if not home:
            raise CommandError('Run bootstrap_site first.')
        slug = 'demonstration-reading-the-evidence'
        article = ArticlePage.objects.filter(slug=slug).first()
        if article:
            self.stdout.write('Demonstration already exists; left unchanged.')
            return
        subject, _ = Subject.objects.get_or_create(slug='demonstration', defaults={'name': 'Demonstration'})
        series, _ = Series.objects.get_or_create(slug='historys-heroes', defaults={'name': "History's Heroes"})
        article = home.add_child(instance=ArticlePage(title='Demonstration: reading the evidence', slug=slug,
            abstract='A fictional example for testing source exploration, archive filtering, and chronology navigation. Not historical scholarship.',
            publication_date=date(2026, 9, 13), historical_start=1800, historical_end=1820,
            is_demonstration=True, series=series, live=False))
        article.authors.add(ArticleAuthor(name='Demonstration Author', sort_order=0))
        article.sources.add(
            ArticleSource(key='demo-letter', kind='primary', title='Fictional letter, 1802', authors='Example Person', year=1802,
                          bibliography='Example Person. Fictional letter, 1802. Demonstration material only.',
                          annotation='An invented document used to exercise the interface, not evidence of a real event.', sort_order=0),
            ArticleSource(key='demo-study', kind='secondary', title='Fictional interpretation', authors='Example Researcher', year=1815,
                          bibliography='Example Researcher. Fictional interpretation, 1815. Demonstration material only.',
                          annotation='An invented secondary account illustrating how editorial annotations are displayed.', sort_order=1))
        article.subjects.add(subject)
        article.body = [
            ('heading', {'text': 'Examining a claim', 'level': 'h2'}),
            ('paragraph', {'text': '<p>This example demonstrates how a reader can follow a claim to its cited material. The people and documents are fictional.</p>',
                'references': [{'source_key': 'demo-letter', 'locator': 'Example page 1', 'note': 'Demonstration reference.'}]}),
            ('paragraph', {'text': '<p>A secondary account can be compared with the primary source while preserving the article text and bibliography.</p>',
                'references': [{'source_key': 'demo-study', 'locator': 'Example chapter 2', 'note': ''}]}),
        ]
        article.full_clean()
        revision = article.save_revision()
        if options['publish_demo']:
            revision.publish()
        timeline = ChronologyPage.objects.filter(slug='historys-heroes').first()
        timeline.is_demonstration = True
        timeline.events.add(
            ChronologyEvent(key='demo-event-one', year=1802, date_label='1802 (fictional)', person='Example Person',
                theme='writing', title='A fictional letter is written', description='Invented event for testing the chronology interface.',
                source_citation='Fictional letter, example page 1. Not historical evidence.', related_article=article, sort_order=0),
            ChronologyEvent(key='demo-event-two', year=1815, date_label='1815 (fictional)', person='Example Researcher',
                theme='context', title='A fictional interpretation appears', description='Invented event for comparing two chronology entries.',
                source_citation='Fictional interpretation, example chapter 2. Not historical evidence.', related_article=article, sort_order=1))
        timeline_revision = timeline.save_revision()
        if options['publish_demo']:
            timeline_revision.publish()
        self.stdout.write('Fictional demonstrations created as ' + ('published pages.' if options['publish_demo'] else 'draft revisions.'))
