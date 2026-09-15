# Initial migration with frozen v1 block definitions. Validate with makemigrations --check before deployment.
from django.db import migrations, models
from django.core.validators import RegexValidator
import django.db.models.deletion
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.fields import RichTextField, StreamField
from apps.journal.models import validate_year
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

class ReferenceBlock(blocks.StructBlock):
    source_key = blocks.CharBlock(help_text="Stable key from this article's Sources tab.", max_length=60)
    locator = blocks.CharBlock(required=False, max_length=160, help_text="Page, chapter, folio, or timestamp.")
    note = blocks.TextBlock(required=False, help_text="An editorial footnote, not an automatically generated claim.")

class ParagraphBlock(blocks.StructBlock):
    text = blocks.RichTextBlock(features=["bold", "italic", "ol", "ul", "link", "superscript", "subscript"])
    references = blocks.ListBlock(ReferenceBlock(), required=False)

class HeadingBlock(blocks.StructBlock):
    text = blocks.CharBlock(max_length=200)
    level = blocks.ChoiceBlock(choices=[("h2", "Section"), ("h3", "Subsection"), ("h4", "Sub-subsection")], default="h2")

class QuoteBlock(blocks.StructBlock):
    text = blocks.TextBlock()
    attribution = blocks.CharBlock(required=False, max_length=240)
    references = blocks.ListBlock(ReferenceBlock(), required=False)

class FigureBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    alt_text = blocks.CharBlock(max_length=250, help_text="Describe the image's relevant content.")
    caption = blocks.CharBlock(required=False, max_length=500)
    credit = blocks.CharBlock(required=False, max_length=250)

class ArticleBodyBlock(blocks.StreamBlock):
    paragraph = ParagraphBlock()
    heading = HeadingBlock()
    quote = QuoteBlock()
    figure = FigureBlock()

KEY_VALIDATOR = RegexValidator(r"^[a-z0-9][a-z0-9-]{0,59}$", "Use lowercase letters, digits, and hyphens; begin with a letter or digit.")
ORCID_VALIDATOR = RegexValidator(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$", "Enter an ORCID in its hyphenated 16-character form.")
SOURCE_KINDS = [("primary", "Primary"), ("secondary", "Secondary")]
THEMES = [("life", "Life"), ("writing", "Writings"), ("politics", "Political activity"), ("context", "Historical context")]


class Migration(migrations.Migration):
    initial = True
    dependencies = [("wagtailcore", "0040_page_draft_title"), ("wagtailimages", "0001_initial")]
    operations = [
        migrations.CreateModel(name='Subject', fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True))
            ], options={'abstract': False, 'ordering': ['name']}, bases=(models.Model,)),
        migrations.CreateModel(name='Series', fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField(blank=True))
            ], options={'abstract': False, 'ordering': ['name'], 'verbose_name_plural': 'series'}, bases=(models.Model,)),
        migrations.CreateModel(name='HomePage', fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('introduction', RichTextField(blank=True, features=["bold", "italic", "link"]))
            ], options={"abstract": False}, bases=('wagtailcore.page',)),
        migrations.CreateModel(name='StandardPage', fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('body', RichTextField(blank=True, features=["h2", "h3", "h4", "bold", "italic", "ol", "ul", "link"]))
            ], options={"abstract": False}, bases=('wagtailcore.page',)),
        migrations.CreateModel(name='ArticlePage', fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('abstract', models.TextField(max_length=3000)),
                ('publication_date', models.DateField()),
                ('historical_start', models.IntegerField(null=True, blank=True, validators=[validate_year])),
                ('historical_end', models.IntegerField(null=True, blank=True, validators=[validate_year])),
                ('series', models.ForeignKey('journal.series', null=True, blank=True, on_delete=models.SET_NULL, related_name="articles")),
                ('subjects', ParentalManyToManyField('journal.subject', blank=True, related_name="articles")),
                ('license_label', models.CharField(max_length=160, default="All rights reserved")),
                ('body', StreamField(ArticleBodyBlock(), blank=True)),
                ('is_demonstration', models.BooleanField(default=False, help_text="Show a prominent non-scholarly demonstration label."))
            ], options={'abstract': False, 'indexes': [models.Index(fields=['publication_date'], name='article_pub_date_idx')]}, bases=('wagtailcore.page',)),
        migrations.CreateModel(name='ArticleAuthor', fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('page', ParentalKey('journal.articlepage', on_delete=models.CASCADE, related_name="authors")),
                ('name', models.CharField(max_length=160)),
                ('affiliation', models.CharField(max_length=250, blank=True)),
                ('orcid', models.CharField(max_length=19, blank=True, validators=[ORCID_VALIDATOR]))
            ], options={'abstract': False, 'ordering': ['sort_order']}, bases=(models.Model,)),
        migrations.CreateModel(name='ArticleSource', fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('page', ParentalKey('journal.articlepage', on_delete=models.CASCADE, related_name="sources")),
                ('key', models.CharField(max_length=60, validators=[KEY_VALIDATOR], help_text="Stable citation key, e.g. letter-01. Do not rename after publication without updating references.")),
                ('kind', models.CharField(max_length=12, choices=SOURCE_KINDS)),
                ('title', models.CharField(max_length=500)),
                ('authors', models.CharField(max_length=500, blank=True)),
                ('year', models.IntegerField(null=True, blank=True, validators=[validate_year])),
                ('bibliography', models.TextField(help_text="Full human-reviewed bibliographic entry, including edition/publisher when relevant.")),
                ('annotation', models.TextField(blank=True, help_text="Explain relevance and limitations; this is public-facing.")),
                ('url', models.URLField(max_length=1000, blank=True))
            ], options={'abstract': False, 'ordering': ['sort_order'], 'constraints': [models.UniqueConstraint(fields=['page','key'], name='article_source_key_unique')]}, bases=(models.Model,)),
        migrations.CreateModel(name='ResearchArchivePage', fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('introduction', models.TextField(blank=True))
            ], options={"abstract": False}, bases=('wagtailcore.page',)),
        migrations.CreateModel(name='ChronologyPage', fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.page')),
                ('introduction', models.TextField(blank=True)),
                ('is_demonstration', models.BooleanField(default=False))
            ], options={"abstract": False}, bases=('wagtailcore.page',)),
        migrations.CreateModel(name='ChronologyEvent', fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('page', ParentalKey('journal.chronologypage', on_delete=models.CASCADE, related_name="events")),
                ('key', models.CharField(max_length=60, validators=[KEY_VALIDATOR])),
                ('year', models.IntegerField(validators=[validate_year])),
                ('date_label', models.CharField(max_length=100, help_text="Human-readable precision, e.g. circa 1790 or 3 March 1850.")),
                ('person', models.CharField(max_length=160)),
                ('theme', models.CharField(max_length=16, choices=THEMES)),
                ('title', models.CharField(max_length=250)),
                ('description', models.TextField()),
                ('source_citation', models.TextField(help_text="Evidence supporting the event and its date.")),
                ('source_url', models.URLField(max_length=1000, blank=True)),
                ('related_article', models.ForeignKey('journal.articlepage', blank=True, null=True, on_delete=models.SET_NULL, related_name="chronology_events"))
            ], options={'abstract': False, 'ordering': ['sort_order'], 'constraints': [models.UniqueConstraint(fields=['page','key'], name='chronology_event_key_unique')]}, bases=(models.Model,)),
    ]
