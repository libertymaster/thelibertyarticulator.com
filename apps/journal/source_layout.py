"""Allowlisted source layouts with revision-owned, HTML-escaped editable text.

The source compiler preserves structural HTML/CSS in reviewed templates. Editors
change text and links in Wagtail; they cannot inject HTML or choose a file path.
"""
import json
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from wagtail import blocks

CONTENT = Path(__file__).resolve().parents[2] / 'content' / 'founding'

TAG_LABELS = {
    'h1': 'Heading',
    'h2': 'Heading',
    'h3': 'Heading',
    'h4': 'Heading',
    'p': 'Paragraph',
    'span': 'Text',
    'strong': 'Emphasis',
    'small': 'Supporting text',
    'a': 'Link text',
    'dt': 'Label',
    'dd': 'Value',
    'li': 'List item',
    'blockquote': 'Quotation',
}


@lru_cache(maxsize=1)
def layout_registry():
    return json.loads((CONTENT / 'layout_registry.json').read_text())


@lru_cache(maxsize=1)
def source_pages():
    return json.loads((CONTENT / 'pages.json').read_text())


def safe_editorial_url(value):
    if not isinstance(value, str) or not value or re.search(r'[\x00-\x20\\\\]', value):
        raise ValidationError('Use an HTTPS/HTTP URL, a root-relative path, or an anchor without whitespace.')
    parts = urlsplit(value)
    if value.startswith('#'):
        return value
    if value.startswith('/') and not value.startswith('//'):
        return value
    if parts.scheme not in {'https', 'http'} or not parts.hostname or parts.username or parts.password:
        raise ValidationError('Only HTTP/HTTPS links, same-site paths, and anchors are allowed.')
    return value


def editor_label(raw, fallback):
    """Turn import provenance labels into short human-facing editor labels."""
    raw = (raw or '').strip()
    if not raw or raw.startswith(('[', '{')) or len(raw) > 180:
        return fallback
    prefix, separator, text = raw.partition(':')
    if separator and prefix in TAG_LABELS:
        text = text.strip()
        return f"{TAG_LABELS[prefix]}: {text}" if text else TAG_LABELS[prefix]
    return raw


def section_editor_label(value):
    layout = ((value.get('layout') if value else '') or '')
    spec = layout_registry().get(layout, {})
    fallback = spec.get('label') or layout or 'Editorial section'
    texts = ((value.get('texts') if value else None) or [])

    # Prefer a structural heading when the imported source supplied one.
    for heading in ('h1:', 'h2:', 'h3:', 'h4:'):
        for item in texts:
            raw = ((item.get('label') if item else '') or '')
            if raw.startswith(heading):
                return editor_label(raw, fallback)

    for item in texts:
        label = editor_label(((item.get('label') if item else '') or ''), '')
        if label:
            return label
    return fallback


class EditorialTextBlock(blocks.StructBlock):
    key = blocks.CharBlock(help_text='Internal layout key. Keep this value unchanged.')
    label = blocks.CharBlock(required=False, help_text='Editor-facing description, not displayed on the site.')
    text = blocks.TextBlock(
        required=False,
        label='Text',
        help_text='Plain text. Formatting is supplied by the layout, not HTML.',
    )

    def get_form_context(self, value, prefix='', errors=None):
        context = super().get_form_context(value, prefix=prefix, errors=errors)
        context['editor_label'] = editor_label(
            ((value.get('label') if value else '') or ''),
            'Text',
        )
        context['internal_key'] = ((value.get('key') if value else '') or '')
        return context

    class Meta:
        label = 'Text'
        label_format = '{label}'
        collapsed = True
        form_template = 'journal/block_forms/editorial_text.html'


class EditorialLinkBlock(blocks.StructBlock):
    key = blocks.CharBlock(help_text='Internal layout key. Keep this value unchanged.')
    label = blocks.CharBlock(required=False)
    url = blocks.CharBlock(
        label='Destination',
        validators=[safe_editorial_url],
        max_length=2000,
    )

    def get_form_context(self, value, prefix='', errors=None):
        context = super().get_form_context(value, prefix=prefix, errors=errors)
        raw_label = ((value.get('label') if value else '') or '')
        context['editor_label'] = editor_label(raw_label, 'Link destination')
        context['internal_key'] = value.get('key', '') if value else ''
        return context

    class Meta:
        label = 'Link'
        label_format = '{url}'
        collapsed = True
        form_template = 'journal/block_forms/editorial_link.html'


class SourceSectionBlock(blocks.StructBlock):
    layout = blocks.CharBlock(help_text='Imported layout ID. Do not change this or its text/link keys.')
    texts = blocks.ListBlock(EditorialTextBlock(), required=False, label='Text')
    links = blocks.ListBlock(EditorialLinkBlock(), required=False, label='Links')

    def get_form_context(self, value, prefix='', errors=None):
        context = super().get_form_context(value, prefix=prefix, errors=errors)
        context['section_label'] = section_editor_label(value)
        context['internal_layout'] = ((value.get('layout') if value else '') or '')
        return context

    def clean(self, value):
        value = super().clean(value)
        spec = layout_registry().get(value['layout'])
        if spec is None:
            raise blocks.StructBlockValidationError(block_errors={'layout': ValidationError('Unknown source layout.')})
        errors = {}
        for field in ('texts', 'links'):
            keys = [item['key'] for item in value[field]]
            if len(keys) != len(set(keys)) or set(keys) != set(spec[field]):
                errors[field] = ValidationError('Keep all original layout keys, once each. Edit their values instead.')
        if errors:
            raise blocks.StructBlockValidationError(block_errors=errors)
        return value

    def get_template(self, value, context=None):
        try:
            return layout_registry()[value['layout']]['template']
        except KeyError as exc:
            raise ValueError('Unknown source layout; refusing an arbitrary template path.') from exc

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        context['fragment'] = {item['key']: item['text'] for item in value['texts']}
        # Validate on read as well: ORM/import writes do not necessarily call clean().
        context['link'] = {item['key']: safe_editorial_url(item['url']) for item in value['links']}
        return context

    class Meta:
        icon = 'doc-full'
        label = 'Editorial section'
        form_template = 'journal/block_forms/source_section.html'


class SourceLayoutStreamBlock(blocks.StreamBlock):
    section = SourceSectionBlock()
