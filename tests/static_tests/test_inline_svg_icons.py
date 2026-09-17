from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAYOUTS = ROOT / 'templates' / 'imported' / 'layouts'

EXPECTED_SVG_COUNTS = {
    'home-03.html': 3,
    'sources-02.html': 4,
    'standards-02.html': 1,
    'standards-05.html': 3,
    'standards-09.html': 4,
    'about-03.html': 4,
    'submit-02.html': 1,
    'submit-04.html': 7,
}

EXPECTED_ICON_CLASSES = {
    'home-03.html': {'lucide-book-open-text', 'lucide-scale', 'lucide-git-compare-arrows'},
    'sources-02.html': {'lucide-archive', 'lucide-fingerprint', 'lucide-file-check-2', 'lucide-key-round'},
    'standards-02.html': {'lucide-circle-dashed'},
    'standards-05.html': {'lucide-eye-off', 'lucide-scale', 'lucide-git-compare-arrows'},
    'standards-09.html': {'lucide-check'},
    'about-03.html': {'lucide-landmark', 'lucide-network', 'lucide-eye', 'lucide-shield-check'},
    'submit-02.html': {'lucide-clock-3'},
    'submit-04.html': {'lucide-check'},
}


def test_imported_icon_templates_render_inline_svg_not_text_placeholders():
    for filename, expected_count in EXPECTED_SVG_COUNTS.items():
        text = (LAYOUTS / filename).read_text()
        assert text.count('<svg') == expected_count, filename
        assert 'class="ui-symbol"' not in text, filename
        assert text.count('aria-hidden="true"') >= expected_count, filename


def test_imported_icon_templates_use_expected_lucide_shapes():
    for filename, icon_classes in EXPECTED_ICON_CLASSES.items():
        text = (LAYOUTS / filename).read_text()
        for icon_class in icon_classes:
            assert icon_class in text, f'{filename}: missing {icon_class}'
