from apps.journal.source_layout import editor_label, section_editor_label


def test_editor_label_humanizes_import_provenance():
    assert editor_label(
        'h2: A journal measured by what it publishes.',
        'Text',
    ) == 'Heading: A journal measured by what it publishes.'
    assert editor_label(
        'p: Ten commissioning briefs make the balance visible.',
        'Text',
    ) == 'Paragraph: Ten commissioning briefs make the balance visible.'


def test_editor_label_hides_parser_dump_labels():
    assert editor_label(
        "[{'tag': 'span', 'props': {'children': ['History']}}]",
        'Link destination',
    ) == 'Link destination'


def test_section_editor_label_prefers_a_real_heading():
    value = {
        'layout': 'home-05',
        'texts': [
            {'key': 't001', 'label': 'p: Founding portfolio', 'text': 'Founding portfolio'},
            {
                'key': 't002',
                'label': 'h2: A journal measured by what it publishes.',
                'text': 'A journal measured by what it publishes.',
            },
        ],
        'links': [],
    }
    assert section_editor_label(value) == 'Heading: A journal measured by what it publishes.'


def test_editor_labels_handle_wagtail_empty_defaults():
    assert editor_label(None, 'Text') == 'Text'
    assert section_editor_label({
        'layout': None,
        'texts': [
            {'key': None, 'label': None, 'text': None},
        ],
        'links': [],
    }) == 'Editorial section'
