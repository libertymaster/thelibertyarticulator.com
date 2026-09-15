# Additive migration: no content is imported or published by migrate.
from django.db import migrations, models
from django.db.models import deletion
from django.core.validators import RegexValidator
from modelcluster.fields import ParentalKey
from wagtail.fields import StreamField
from apps.journal.source_layout import SourceLayoutStreamBlock, safe_editorial_url

KEY_VALIDATOR = RegexValidator(r"^[a-z0-9][a-z0-9-]{0,59}$", "Use lowercase letters, digits, and hyphens; begin with a letter or digit.")

class Migration(migrations.Migration):
    dependencies = [("journal", "0001_initial")]
    operations = [
        migrations.AddField(model_name='homepage', name="reference_layout", field=StreamField(SourceLayoutStreamBlock(), blank=True)),
        migrations.AddField(model_name='standardpage', name="reference_layout", field=StreamField(SourceLayoutStreamBlock(), blank=True)),
        migrations.AddField(model_name='articlepage', name="reference_layout", field=StreamField(SourceLayoutStreamBlock(), blank=True)),
        migrations.AddField(model_name='researcharchivepage', name="reference_layout", field=StreamField(SourceLayoutStreamBlock(), blank=True)),
        migrations.AddField(model_name="homepage", name='header_layout', field=StreamField(SourceLayoutStreamBlock(), blank=True)),
        migrations.AddField(model_name="homepage", name='footer_layout', field=StreamField(SourceLayoutStreamBlock(), blank=True)),
        migrations.AddField(model_name="homepage", name="artwork_url", field=models.CharField(max_length=2000, blank=True, validators=[safe_editorial_url])),
        migrations.AddField(model_name="homepage", name="artwork_alt", field=models.CharField(max_length=300, blank=True)),
        migrations.AlterField(model_name="articlepage", name="publication_date", field=models.DateField(null=True, blank=True)),
        migrations.AddField(model_name="articlepage", name='dek', field=models.TextField(blank=True)),
        migrations.AddField(model_name="articlepage", name='discipline', field=models.CharField(max_length=20, blank=True, choices=[("History", "History"), ("Philosophy", "Philosophy"), ("Politics", "Politics")])),
        migrations.AddField(model_name="articlepage", name='article_type', field=models.CharField(max_length=100, default="Article")),
        migrations.AddField(model_name="articlepage", name='record_status', field=models.CharField(max_length=30, choices=[("public_draft", "Public draft"), ("planned", "Planned"), ("under_review", "Under review"), ("version_of_record", "Version of record")], default="public_draft")),
        migrations.AddField(model_name="articlepage", name='review_status', field=models.CharField(max_length=200, default="Review status not declared")),
        migrations.AddField(model_name="articlepage", name='version_label', field=models.CharField(max_length=50, blank=True)),
        migrations.AddField(model_name="articlepage", name='sources_summary', field=models.CharField(max_length=500, blank=True)),
        migrations.AddField(model_name="articlepage", name='method', field=models.CharField(max_length=200, blank=True)),
        migrations.AddField(model_name="articlepage", name='display_date', field=models.CharField(max_length=100, blank=True)),
        migrations.AddField(model_name="articlepage", name='read_time', field=models.CharField(max_length=80, blank=True)),
        migrations.AlterField(model_name="articlesource", name="kind", field=models.CharField(max_length=12, choices=[("primary", "Primary"), ("secondary", "Secondary"), ("unclassified", "Not classified")])),
        migrations.AddField(model_name="articlesource", name="display_title", field=models.CharField(max_length=500, blank=True, help_text="Optional short title for the source ledger.")),
        migrations.AddField(model_name="articlesource", name="edition_label", field=models.CharField(max_length=500, blank=True)),
        migrations.AddField(model_name="articlesource", name="use_description", field=models.TextField(blank=True)),
        migrations.AddField(model_name="articlesource", name="verification_status", field=models.CharField(max_length=500, blank=True)),
        migrations.CreateModel(name="SectionIndexPage", fields=[
            ("page_ptr", models.OneToOneField(auto_created=True, on_delete=deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to="wagtailcore.page")),
        ], options={"abstract": False}, bases=("wagtailcore.page",)),
        migrations.CreateModel(name="ImportedCitation", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("sort_order", models.IntegerField(blank=True, editable=False, null=True)),
            ("page", ParentalKey(on_delete=deletion.CASCADE, related_name="imported_citations", to="journal.articlepage")),
            ("source_key", models.CharField(max_length=60, validators=[KEY_VALIDATOR])),
            ("number", models.PositiveIntegerField()),
            ("note_anchor", models.CharField(max_length=60, validators=[KEY_VALIDATOR])),
            ("passage_anchor", models.CharField(max_length=60, validators=[KEY_VALIDATOR])),
            ("locator", models.CharField(max_length=160, blank=True)),
            ("note", models.TextField(blank=True)),
        ], options={"abstract": False, "ordering": ["sort_order"], "constraints": [models.UniqueConstraint(fields=["page", "number"], name="imported_citation_number_unique")]}),
        migrations.CreateModel(name="ContentImportRecord", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("key", models.CharField(max_length=200, unique=True)),
            ("checksum", models.CharField(max_length=64)),
            ("page", models.ForeignKey(on_delete=deletion.PROTECT, to="wagtailcore.page")),
            ("revision_id", models.PositiveBigIntegerField(null=True)),
            ("imported_at", models.DateTimeField(auto_now_add=True)),
        ]),
    ]
