from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from wagtail.models import Page, Site, GroupPagePermission
from apps.journal.models import HomePage, ResearchArchivePage, ChronologyPage, StandardPage

class Command(BaseCommand):
    help = "Initialize this new publication idempotently; never import or overwrite another publication."
    @transaction.atomic
    def handle(self, *args, **options):
        homes = HomePage.objects.all()
        if homes.count() > 1:
            raise CommandError("Multiple HomePages found; resolve the site configuration manually.")
        root = Page.get_first_root_node()
        home = homes.first()
        if home is None:
            if Page.objects.exclude(pk=root.pk).exclude(slug='home', depth=2).exists():
                raise CommandError("Database contains another publication. Refusing automatic bootstrap.")
            # Remove only Wagtail's untouched stock welcome page on a fresh database.
            for candidate in root.get_children():
                if candidate.slug == 'home' and candidate.content_type.model == 'page' and not candidate.get_children().exists():
                    candidate.delete()
                else:
                    raise CommandError("Root contains an existing site. Use a fresh project/database.")
            home = root.add_child(instance=HomePage(title='The Liberty Articulator', slug='home',
                introduction='<p>Investigating under the microscope of liberty. Analyzing through the telescope of history.</p>', live=False))
            home.save_revision().publish()
        Site.objects.update_or_create(is_default_site=True, defaults={
            'hostname': settings.PUBLIC_HOST, 'port': 80 if settings.DEBUG else 443,
            'root_page': home, 'site_name': 'The Liberty Articulator'})
        for cls, slug, title, attrs in [
            (ResearchArchivePage, 'archive', 'Research archive', {'introduction': 'Search published articles by subject, author, series, source type, publication date, and historical period.'}),
            (ChronologyPage, 'historys-heroes', "History's Heroes", {'introduction': 'Explore evidence-backed events and the articles that examine them.'}),
            (StandardPage, 'standards', 'Editorial standards', {'body': '<p>Editorial policy is being prepared. This placeholder is not a claim of peer review or a completed editorial policy.</p>'}),
        ]:
            if not home.get_children().filter(slug=slug).exists():
                page = home.add_child(instance=cls(title=title, slug=slug, live=False, **attrs))
                page.save_revision().publish()
        access = Permission.objects.filter(codename='access_admin', content_type__app_label='wagtailadmin').first()
        roles = {
            'Contributor': ['add_page'],
            'Reviewer': ['change_page'],
            'Editor': ['add_page', 'change_page', 'publish_page', 'lock_page'],
            'Managing Editor': ['add_page', 'change_page', 'publish_page', 'lock_page', 'unlock_page', 'bulk_delete_page'],
        }
        for name, codes in roles.items():
            group, _ = Group.objects.get_or_create(name=name)
            if access:
                group.permissions.add(access)
            for code in codes:
                permission = Permission.objects.get(codename=code, content_type__app_label='wagtailcore', content_type__model='page')
                GroupPagePermission.objects.get_or_create(group=group, page=home, permission=permission)
        self.stdout.write(self.style.SUCCESS('Site initialized. Configure Wagtail approval tasks/workflows and assign users before publishing.'))
