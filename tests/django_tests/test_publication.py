import json
from datetime import date
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, RequestFactory, override_settings
from wagtail.models import Site, PageViewRestriction
from apps.journal.models import HomePage, ArticlePage, ArticleSource, ArticleAuthor, ChronologyPage
from apps.journal.services import article_context, chronology_payload

class PublicationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('bootstrap_site',verbosity=0)
        call_command('seed_demo',publish_demo=True,verbosity=0)
        cls.home=HomePage.objects.get()
        cls.article=ArticlePage.objects.get(slug='demonstration-reading-the-evidence')
        site=Site.objects.get(is_default_site=True);site.hostname='testserver';site.port=80;site.save()
    def setUp(self):
        self.factory=RequestFactory()
    def archive(self,query=''):
        return self.client.get('/api/v1/archive/'+query)
    def test_server_rendered_article_keeps_evidence(self):
        response=self.client.get('/'+self.article.slug+'/')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'Bibliography')
        self.assertContains(response,'source-demo-letter')
        self.assertContains(response,'sources-data')
        self.assertContains(response,'Fictional letter')
    def test_archive_is_live_only(self):
        page=self.home.add_child(instance=ArticlePage(title='Hidden draft',slug='hidden-draft',abstract='private',publication_date=date.today(),live=False))
        page.save_revision()
        self.assertNotIn(page.pk,[r['id'] for r in self.archive().json()['results']])
    def test_unpublish_removes_result_immediately(self):
        self.article.unpublish()
        self.assertEqual(self.archive().json()['total'],0)
    def test_restricted_page_not_in_results_or_facets(self):
        PageViewRestriction.objects.create(page=self.article,restriction_type='password',password='not-a-public-page')
        payload=self.archive().json()
        self.assertEqual(payload['total'],0)
        self.assertEqual(payload['facets']['authors'],[])
    def test_ancestor_restriction_removes_article(self):
        PageViewRestriction.objects.create(page=self.home,restriction_type='password',password='private-root')
        self.assertEqual(self.archive().json()['total'],0)
    def test_historical_overlap_filter(self):
        self.assertEqual(self.archive('?historical_from=1810&historical_to=1811').json()['total'],1)
        self.assertEqual(self.archive('?historical_from=1850').json()['total'],0)
    def test_no_year_zero(self):
        self.assertEqual(self.archive('?historical_from=0').status_code,400)
    def test_reversed_date_range(self):
        self.assertEqual(self.archive('?published_from=2026-12-01&published_to=2026-01-01').status_code,400)
    def test_read_only_endpoint(self):
        self.assertEqual(self.client.post('/api/v1/archive/').status_code,405)
    def test_source_kind_filters(self):
        self.assertEqual(self.archive('?source_kind=primary').json()['total'],1)
        self.assertEqual(self.archive('?source_kind=invalid').status_code,400)
    def test_missing_reference_rejected(self):
        self.article.body=[('paragraph',{'text':'<p>Claim.</p>','references':[{'source_key':'missing','locator':'','note':''}]})]
        with self.assertRaises(ValidationError): self.article.clean()
    def test_citation_anchors_are_unique(self):
        context=article_context(self.article,self.factory.get('/'))
        anchors=[note['anchor'] for note in context['footnotes']]
        self.assertEqual(len(anchors),len(set(anchors)))
        self.assertEqual(len(anchors),2)
    def test_unpublished_revision_not_visible(self):
        draft=self.article.get_latest_revision_as_object()
        source=draft.sources.get(key='demo-letter');source.annotation='Unpublished confidential revision'
        draft.sources.add(source)
        draft.save_revision()
        fresh=ArticlePage.objects.get(pk=self.article.pk)
        self.assertNotEqual(fresh.sources.get(key='demo-letter').annotation,'Unpublished confidential revision')
        context=article_context(draft,self.factory.get('/'))
        self.assertEqual(context['sources_payload']['sources'][0]['annotation'],'Unpublished confidential revision')
    def test_chronology_hides_unpublished_related_article(self):
        self.article.unpublish()
        payload=chronology_payload(ChronologyPage.objects.get()).model_dump()
        self.assertTrue(all(event['article_url']=='' for event in payload['events']))
    def test_archive_fallback_exists(self):
        response=self.client.get('/archive/?q=demonstration')
        self.assertContains(response,'archive-fallback')
        self.assertContains(response,'method="get"')
        self.assertContains(response,self.article.title)
    def test_invalid_access_assertion_rejected(self):
        with override_settings(REQUIRE_CF_ACCESS=True,EDITOR_HOST='editor.example.org',ALLOWED_HOSTS=['editor.example.org']):
            response=self.client.get('/admin/',HTTP_HOST='editor.example.org')
            self.assertEqual(response.status_code,403)

    def test_submitted_source_reference_uses_new_form_rows(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from apps.journal.editor_forms import ArticlePageForm
        from wagtail.admin.forms import WagtailAdminPageForm
        body = ArticlePage._meta.get_field('body').to_python([
            {'type':'paragraph','value':{'text':'<p>New claim.</p>',
             'references':[{'source_key':'new-source','locator':'p. 2','note':''}]},'id':'sample-block'}
        ])
        source_form = SimpleNamespace(cleaned_data={'key':'new-source'})
        formset = SimpleNamespace(forms=[source_form],is_valid=lambda:True)
        added=[]
        form=SimpleNamespace(formsets={'sources':formset},add_error=lambda field,message:added.append((field,message)))
        # Exercise the form logic without depending on Wagtail's evolving POST widget encoding.
        with patch.object(WagtailAdminPageForm,'clean',return_value={'body':body}):
            actual = ArticlePageForm.__new__(ArticlePageForm)
            actual.formsets=form.formsets
            actual.add_error=form.add_error
            ArticlePageForm.clean(actual)
        self.assertEqual(added,[])

    def test_public_host_cannot_reach_admin(self):
        from django.conf import settings
        response=self.client.get('/admin/',HTTP_HOST=settings.PUBLIC_HOST)
        self.assertEqual(response.status_code,404)
    def test_sitemap_renders(self):
        response=self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code,200)
