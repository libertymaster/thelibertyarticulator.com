"""Run with manage.py test tests.django_tests.test_branding on the locked target."""
from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve

from apps.core.branding_views import branding_asset
from apps.journal.templatetags.journal_tags import publication_branding


@override_settings(
    PUBLIC_ORIGIN="https://staging.example.org",
    STATIC_URL="/static/",
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class BrandingTests(SimpleTestCase):
    def setUp(self):
        self.context = {
            "branding": SimpleNamespace(artwork_url="", artwork_alt=""),
            "page": SimpleNamespace(title="An article", seo_title="", search_description="An abstract",
                                    url="/article/example/", record_status="public_draft"),
        }

    def test_default_metadata_has_complete_image_and_favicon(self):
        html = render_to_string("journal/includes/branding_metadata.html", self.context)
        self.assertIn('content="https://staging.example.org/static/branding/og.png"', html)
        self.assertIn('property="og:image:width" content="1200"', html)
        self.assertIn('property="og:image:height" content="630"', html)
        self.assertIn('href="/static/branding/favicon.svg" type="image/svg+xml"', html)
        self.assertIn('name="twitter:card" content="summary_large_image"', html)
        self.assertEqual(html.count('property="og:image"'), 1)

    def test_custom_image_does_not_inherit_default_dimensions(self):
        self.context["branding"] = SimpleNamespace(artwork_url="/media/custom.webp", artwork_alt='A "custom" image')
        html = render_to_string("journal/includes/branding_metadata.html", self.context)
        self.assertIn('content="https://staging.example.org/media/custom.webp"', html)
        self.assertIn('A &quot;custom&quot; image', html)
        self.assertNotIn('og:image:width', html)
        self.assertNotIn('og:image:type', html)

    def test_figure_uses_the_same_url_as_the_social_card(self):
        html = render_to_string("journal/includes/editorial_artwork.html", self.context)
        assets = publication_branding(self.context)
        self.assertIn('src="' + assets["image_url"] + '"', html)
        self.assertIn('width="1200" height="630"', html)
        self.assertNotIn('missing-asset', html)

    def test_alias_get_and_head_redirect_to_static_file(self):
        factory = RequestFactory()
        for filename in ["og.png", "favicon.svg"]:
            for method in [factory.get, factory.head]:
                response = branding_asset(method('/' + filename), filename)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response["Location"], '/static/branding/' + filename)
                self.assertIn('no-store', response['Cache-Control'])

    def test_alias_rejects_post(self):
        response = branding_asset(RequestFactory().post('/og.png'), 'og.png')
        self.assertEqual(response.status_code, 405)

    def test_root_aliases_precede_wagtail_catchall(self):
        self.assertEqual(resolve('/og.png').url_name, 'branding-og')
        self.assertEqual(resolve('/favicon.svg').url_name, 'branding-favicon')

    def test_preview_context_override_is_used(self):
        self.context['branding'] = SimpleNamespace(artwork_url='/media/draft-preview.png', artwork_alt='Draft image')
        self.assertEqual(publication_branding(self.context)['image_url'], 'https://staging.example.org/media/draft-preview.png')

    def test_editor_host_is_not_used_in_public_metadata(self):
        self.context['page'].url = 'https://editor.example.org/article/example/'
        self.assertEqual(publication_branding(self.context)['page_url'], 'https://staging.example.org/article/example/')
