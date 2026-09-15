from wagtail.admin.forms import WagtailAdminPageForm


class ArticlePageForm(WagtailAdminPageForm):
    """Validate new citations against submitted source rows, not the old live revision."""

    def _post_clean(self):
        # Django calls model.clean before modelcluster saves inline child formsets.
        # The form-level check below uses their cleaned submission instead.
        self.instance._defer_reference_validation = True
        try:
            super()._post_clean()
        finally:
            self.instance._defer_reference_validation = False

    def clean(self):
        cleaned = super().clean()
        source_forms = self.formsets.get("sources")
        body = cleaned.get("body")
        if source_forms is None or body is None or not source_forms.is_valid():
            return cleaned
        keys = [
            form.cleaned_data["key"]
            for form in source_forms.forms
            if form.cleaned_data.get("key") and not form.cleaned_data.get("DELETE")
        ]
        missing = set()
        for block in body:
            if block.block_type in {"paragraph", "quote"}:
                missing.update(
                    ref["source_key"]
                    for ref in block.value["references"]
                    if ref["source_key"] not in keys
                )
        imported_forms = self.formsets.get("imported_citations")
        if imported_forms is not None and imported_forms.is_valid():
            missing.update(
                row.cleaned_data["source_key"]
                for row in imported_forms.forms
                if row.cleaned_data.get("source_key") and not row.cleaned_data.get("DELETE")
                and row.cleaned_data["source_key"] not in keys
            )
        if len(keys) != len(set(keys)):
            self.add_error("body", "Source keys must be unique within this article.")
        if missing:
            self.add_error("body", "Undefined source keys: " + ", ".join(sorted(missing)))
        return cleaned
