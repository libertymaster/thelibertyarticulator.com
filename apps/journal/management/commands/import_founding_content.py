"""Import the supplied founding edition without rewriting existing editorial work."""
import hashlib
import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from wagtail.models import Revision

from apps.journal.models import (
    ArticleAuthor, ArticlePage, ArticleSource, ContentImportRecord, HomePage,
    ImportedCitation, ResearchArchivePage, SectionIndexPage, StandardPage, Subject,
)
from apps.journal.source_layout import CONTENT, source_pages

class Command(BaseCommand):
    help = 'Dry-run by default. --apply saves draft revisions; --publish explicitly makes the imported records public.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--publish', action='store_true')

    def handle(self, *args, **options):
        if options['publish'] and not options['apply']:
            raise CommandError('--publish requires --apply. No changes made.')
        self.publish = options['publish']
        self.pages = source_pages()
        self.data = json.loads((CONTENT / 'journal_data.json').read_text())
        self.evidence = json.loads((CONTENT / 'article_evidence.json').read_text())
        if not options['apply']:
            self.stdout.write('Plan: preserve the supplied home, about, standards, sources, submissions, founding portfolio, and archive copy; import one public-draft editorial and nine PLANNED briefs. No chronology events are supplied. No database changes or publications performed.')
            return
        with transaction.atomic():
            homes = list(HomePage.objects.all())
            if len(homes) != 1:
                raise CommandError('Run bootstrap_site on this NEW project first; exactly one HomePage is required.')
            home = homes[0]
            self.apply_page('home', home, {
                'reference_layout': self.pages['home']['sections'],
                'header_layout': self.pages['header']['sections'],
                'footer_layout': self.pages['footer']['sections'],
                'search_description': 'An independent journal of history, philosophy, and politics, with analysis across every discipline.',
            }, bootstrap=True)
            article_parent = self.container(home, 'article', 'Articles')
            issue_parent = self.container(home, 'issue', 'Issues')
            for name, slug, title, parent in [
                ('about', 'about', 'About', home),
                ('standards', 'standards', 'Research & Editorial Standards', home),
                ('sources', 'sources', 'Sources & Provenance', home),
                ('submit', 'submit', 'Submissions', home),
                ('founding', 'founding', 'Founding Issue Portfolio', issue_parent),
            ]:
                existing = parent.get_children().filter(slug=slug).specific().first()
                if existing and not isinstance(existing, StandardPage):
                    raise CommandError(f'Existing /{slug}/ has a different page type. No content replaced.')
                page = existing or parent.add_child(instance=StandardPage(title=title, slug=slug, live=False))
                self.apply_page(name, page, {
                    'title': title,
                    'reference_layout': self.pages[name]['sections'],
                    'search_description': self.pages[name]['metadata'].get('description', ''),
                }, bootstrap=bool(existing and name == 'standards'), new=existing is None)
            archive = home.get_children().filter(slug='archive').specific().first()
            if not isinstance(archive, ResearchArchivePage):
                raise CommandError('Expected the bootstrap ResearchArchivePage at /archive/.')
            self.apply_page('archive', archive, {
                'reference_layout': self.pages['archive']['sections'],
                'search_description': self.pages['archive']['metadata'].get('description', ''),
            }, bootstrap=True)
            for entry in self.data['publications']:
                self.article(article_parent, entry)
        self.stdout.write(self.style.SUCCESS('Source import complete. Existing import records and subsequent editor changes were preserved.'))
        if not self.publish:
            self.stdout.write('Imported revisions remain drafts. Preview and publish deliberately in Wagtail.')

    def checksum(self, payload):
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    def existing_import(self, key, payload):
        record = ContentImportRecord.objects.filter(key='founding-v1/' + key).select_related('page').first()
        if record is None:
            return False
        if record.checksum != self.checksum(payload):
            raise CommandError(f'Source changed for {key}; refusing to overwrite an existing import. Use a reviewed content migration.')
        if self.publish and record.revision_id and record.page.live_revision_id != record.revision_id:
            if record.page.latest_revision_id != record.revision_id:
                self.stdout.write(f'Preserved editor changes: {key}. Publish its current revision in Wagtail.')
            else:
                Revision.objects.get(pk=record.revision_id).publish()
        self.stdout.write(f'Already imported; preserved: {key}')
        return True

    def save_record(self, key, page, payload):
        revision = page.save_revision()
        if self.publish:
            revision.publish()
        ContentImportRecord.objects.create(key='founding-v1/' + key, checksum=self.checksum(payload), page=page, revision_id=revision.pk)
        self.stdout.write(('Public: ' if self.publish else 'Draft revision: ') + key)

    def apply_page(self, key, page, attrs, bootstrap=False, new=False):
        if self.existing_import(key, attrs):
            return
        if not new:
            if not bootstrap or getattr(page, 'reference_layout', None) or page.has_unpublished_changes:
                raise CommandError(f'Existing edited page at {key}; refusing automatic replacement.')
            # Only the exact unedited 0.2.0 bootstrap text may be adopted automatically.
            if key == 'home' and str(page.introduction) != '<p>Investigating under the microscope of liberty. Analyzing through the telescope of history.</p>':
                raise CommandError('Home introduction differs from the original bootstrap. Import into a fresh test project.')
            if key == 'standards' and str(page.body) != '<p>Editorial policy is being prepared. This placeholder is not a claim of peer review or a completed editorial policy.</p>':
                raise CommandError('Standards has existing editorial content; it was not replaced.')
            if key == 'archive' and page.introduction != 'Search published articles by subject, author, series, source type, publication date, and historical period.':
                raise CommandError('Archive has existing editorial content; it was not replaced.')
        for name, value in attrs.items():
            setattr(page, name, value)
        self.save_record(key, page, attrs)

    def container(self, home, slug, title):
        key = 'container-' + slug
        payload = {'title': title, 'slug': slug}
        existing = home.get_children().filter(slug=slug).specific().first()
        if self.existing_import(key, payload):
            if not isinstance(existing, SectionIndexPage):
                raise CommandError(f'Imported container /{slug}/ was moved or replaced. Reconcile manually.')
            return existing
        if existing:
            raise CommandError(f'Existing /{slug}/ is not owned by this importer.')
        page = home.add_child(instance=SectionIndexPage(title=title, slug=slug, live=False))
        self.save_record(key, page, payload)
        return page

    def article(self, parent, entry):
        key = 'publication-' + entry['slug']
        is_editorial = entry['slug'] == 'the-archive-is-not-the-village'
        payload = {'entry': entry, 'layout': self.pages['article']['sections'] if is_editorial else [], 'evidence': self.evidence if is_editorial else {}}
        if self.existing_import(key, payload):
            return
        if parent.get_children().filter(slug=entry['slug']).exists():
            raise CommandError(f'Existing article slug {entry["slug"]}; no overwrite performed.')
        article = ArticlePage(
            title=entry['title'], slug=entry['slug'], live=False,
            abstract=self.evidence['abstract'] if is_editorial else entry['deck'],
            dek=entry['deck'], publication_date=date(2026, 8, 29) if is_editorial else None,
            discipline=entry['discipline'], article_type=entry['type'],
            record_status='public_draft' if is_editorial else 'planned',
            review_status=entry['review'], version_label='1.0' if is_editorial else '',
            sources_summary=entry['sources'], method=entry['method'],
            display_date=entry['date'], read_time=entry['readTime'],
            search_description=self.pages['article']['metadata']['description'] if is_editorial else entry['deck'],
            license_label='Content rights are being established.',
            reference_layout=self.pages['article']['sections'] if is_editorial else [],
        )
        article = parent.add_child(instance=article)
        article.authors.add(ArticleAuthor(name=entry['author'], affiliation='The Liberty Articulator' if is_editorial else '', sort_order=0))
        subject, _ = Subject.objects.get_or_create(slug=slugify(entry['discipline']), defaults={'name': entry['discipline']})
        article.subjects.add(subject)
        if is_editorial:
            for source in self.evidence['sources']:
                article.sources.add(ArticleSource(**source))
            for citation in self.evidence['citations']:
                article.imported_citations.add(ImportedCitation(**citation))
        article.full_clean()
        self.save_record(key, article, payload)
