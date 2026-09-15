import io
from datetime import date

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from wagtail.models import Site, PageViewRestriction

from apps.journal.models import ArticlePage, ContentImportRecord, HomePage


class FoundingImportTests(TestCase):
    def setUp(self):
        call_command('bootstrap_site', stdout=io.StringIO())
        self.home = HomePage.objects.get()
        site = Site.objects.get(is_default_site=True)
        site.hostname, site.port = 'testserver', 80
        site.save()

    def run_import(self, **options):
        call_command('import_founding_content', stdout=io.StringIO(), **options)

    def test_dry_run_does_not_mutate_or_publish(self):
        self.run_import()
        self.assertEqual(ContentImportRecord.objects.count(), 0)
        self.assertEqual(ArticlePage.objects.count(), 0)

    def test_apply_is_draft_only_and_idempotent(self):
        self.run_import(apply=True)
        self.assertEqual(ContentImportRecord.objects.count(), 19)
        self.assertEqual(ArticlePage.objects.live().count(), 0)
        self.run_import(apply=True)
        self.assertEqual(ArticlePage.objects.count(), 10)
        self.assertEqual(self.client.get('/api/v1/archive/').json()['total'], 0)

    def test_explicit_publish_can_follow_a_draft_import(self):
        self.run_import(apply=True)
        self.run_import(apply=True, publish=True)
        self.assertEqual(ArticlePage.objects.live().count(), 10)
        self.assertContains(self.client.get('/'), 'Analyzing through the')
        self.assertEqual(self.client.get('/api/v1/archive/?status=planned').json()['total'], 9)
        self.assertEqual(self.client.get('/api/v1/archive/?status=public_draft').json()['total'], 1)
        self.assertTrue(all(not p.publication_date for p in ArticlePage.objects.filter(record_status='planned')))

    def test_import_will_not_overwrite_editor_changes(self):
        self.run_import(apply=True, publish=True)
        page = ArticlePage.objects.get(slug='the-archive-is-not-the-village')
        published_title = page.title
        published_revision_id = page.live_revision_id
        expected_draft_title = 'An editor changed this draft'

        # Wagtail may return the same Page instance when no draft changes exist.
        # Keep expected values independent of that instance and its later refresh.
        draft = page.get_latest_revision_as_object()
        draft.title = expected_draft_title
        revision = draft.save_revision()
        revision.refresh_from_db()
        self.assertEqual(revision.content['title'], expected_draft_title)

        self.run_import(apply=True, publish=True)
        page.refresh_from_db()
        revision.refresh_from_db()

        # Verify persisted draft content, not a mutable in-memory alias of page.
        self.assertEqual(page.latest_revision_id, revision.pk)
        self.assertEqual(page.live_revision_id, published_revision_id)
        self.assertEqual(page.title, published_title)
        self.assertTrue(page.live)
        self.assertTrue(page.has_unpublished_changes)
        self.assertEqual(page.draft_title, expected_draft_title)
        self.assertEqual(revision.content['title'], expected_draft_title)
        self.assertEqual(
            page.get_latest_revision_as_object().title, expected_draft_title
        )

    def test_public_article_has_sources_and_original_anchors(self):
        self.run_import(apply=True, publish=True)
        response = self.client.get('/article/the-archive-is-not-the-village/')
        self.assertEqual(response.status_code, 200)
        for marker in ['note-1', 'source-imported-4', 'sources-data', 'source-ledger', 'not externally']:
            self.assertContains(response, marker)
        self.assertNotContains(response, 'src="/og.png"')
        self.assertContains(response, '/static/branding/og.png')
        self.assertContains(response, '/static/branding/favicon.svg')
        self.assertNotContains(response, 'Editorial artwork was referenced in the supplied source')

    def test_withdrawn_or_restricted_article_does_not_leak_into_archive(self):
        self.run_import(apply=True, publish=True)
        page = ArticlePage.objects.get(slug='the-archive-is-not-the-village')
        PageViewRestriction.objects.create(page=page, restriction_type='password', password='private')
        self.assertEqual(self.client.get('/api/v1/archive/?status=public_draft').json()['total'], 0)

    def test_planned_status_date_validation_applies_in_admin(self):
        page = ArticlePage(title='Plan', abstract='Plan', record_status='planned', publication_date=date.today())
        page._defer_reference_validation = True
        with self.assertRaises(ValidationError):
            page.clean()

    def test_existing_custom_home_is_preserved(self):
        self.home.introduction = '<p>Existing work.</p>'
        self.home.save_revision().publish()
        with self.assertRaises(CommandError):
            self.run_import(apply=True)
        self.assertEqual(ContentImportRecord.objects.count(), 0)

    def test_imported_source_revision_updates_both_notes_and_panel(self):
        self.run_import(apply=True, publish=True)
        page = ArticlePage.objects.get(slug='the-archive-is-not-the-village')
        source = page.sources.get(key='imported-1')
        source.bibliography = 'Revised bibliographic entry'
        page.sources.add(source)
        page.save_revision().publish()
        response = self.client.get('/article/the-archive-is-not-the-village/')
        self.assertContains(response, 'Revised bibliographic entry', count=2)
