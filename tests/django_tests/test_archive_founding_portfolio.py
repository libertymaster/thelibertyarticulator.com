import io

from django.core.management import call_command
from django.test import TestCase
from wagtail.models import Revision, Site

from apps.journal.models import ArticlePage, ResearchArchivePage, SectionIndexPage


class ArchiveFoundingPortfolioTests(TestCase):
    def setUp(self):
        call_command("bootstrap_site", stdout=io.StringIO())
        site = Site.objects.get(is_default_site=True)
        site.hostname, site.port = "testserver", 80
        site.save()
        call_command("import_founding_content", apply=True, stdout=io.StringIO())

        archive = ResearchArchivePage.objects.get(slug="archive")
        Revision.objects.get(pk=archive.latest_revision_id).publish()

        article_index = SectionIndexPage.objects.get(slug="article")
        Revision.objects.get(pk=article_index.latest_revision_id).publish()

        editorial = ArticlePage.objects.get(slug="the-archive-is-not-the-village")
        Revision.objects.get(pk=editorial.latest_revision_id).publish()

    def test_archive_renders_curated_portfolio_without_publishing_planned_briefs(self):
        response = self.client.get("/archive/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Founding portfolio")
        self.assertContains(response, 'id="archive-portfolio-', count=10)
        self.assertContains(response, "Planned commissioning brief", count=9)
        self.assertContains(
            response,
            'href="/article/the-archive-is-not-the-village/"',
        )
        self.assertNotContains(
            response,
            'href="/article/petitioning-before-independence/"',
        )

        self.assertEqual(
            self.client.get("/api/v1/archive/?status=public_draft").json()["total"],
            1,
        )
        self.assertEqual(
            self.client.get("/api/v1/archive/?status=planned").json()["total"],
            0,
        )
