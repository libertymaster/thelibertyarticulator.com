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

@lru_cache(maxsize=1)
def layout_registry():
    return json.loads((CONTENT / 'layout_registry.json').read_text())

@lru_cache(maxsize=1)
def source_pages():
    return json.loads((CONTENT / 'pages.json').read_text())

def safe_editorial_url(value):
    if not isinstance(value, str) or not value or re.search(r'[\x00-\x20\\]', value):
        raise ValidationError('Use an HTTPS/HTTP URL, a root-relative path, or an anchor without whitespace.')
    parts = urlsplit(value)
    if value.startswith('#'):
        return value
    if value.startswith('/') and not value.startswith('//'):
        return value
    if parts.scheme not in {'https', 'http'} or not parts.hostname or parts.username or parts.password:
        raise ValidationError('Only HTTP/HTTPS links, same-site paths, and anchors are allowed.')
    return value

class EditorialTextBlock(blocks.StructBlock):
    key = blocks.CharBlock(help_text='Layout key. Keep this value unchanged.')
    label = blocks.CharBlock(required=False, help_text='Editor-facing description, not displayed on the site.')
    text = blocks.TextBlock(required=False, help_text='Plain text. Formatting is supplied by the layout, not HTML.')
    class Meta:
        label = 'Text fragment'

class EditorialLinkBlock(blocks.StructBlock):
    key = blocks.CharBlock(help_text='Layout key. Keep this value unchanged.')
    label = blocks.CharBlock(required=False)
    url = blocks.CharBlock(validators=[safe_editorial_url], max_length=2000)
    class Meta:
        label = 'Link target'

class SourceSectionBlock(blocks.StructBlock):
    layout = blocks.CharBlock(help_text='Imported layout ID. Do not change this or its text/link keys.')
    texts = blocks.ListBlock(EditorialTextBlock(), required=False)
    links = blocks.ListBlock(EditorialLinkBlock(), required=False)
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
        label = 'Imported editorial section'

class SourceLayoutStreamBlock(blocks.StreamBlock):
    section = SourceSectionBlock()
