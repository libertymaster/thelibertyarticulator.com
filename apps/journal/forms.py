from django import forms
from .models import validate_year

class ArchiveForm(forms.Form):
    q = forms.CharField(required=False, max_length=120, label="Search title or abstract")
    subject = forms.CharField(required=False, max_length=100)
    author = forms.CharField(required=False, max_length=160)
    series = forms.CharField(required=False, max_length=100)
    source_kind = forms.ChoiceField(required=False, choices=[("", "Any source type"), ("primary", "Primary sources"), ("secondary", "Secondary sources"), ("unclassified", "Not classified")])
    published_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    published_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    historical_from = forms.IntegerField(required=False, validators=[validate_year], label="Historical period from (negative = BCE)")
    historical_to = forms.IntegerField(required=False, validators=[validate_year], label="Historical period to (negative = BCE)")
    sort = forms.ChoiceField(required=False, choices=[("newest", "Newest published"), ("oldest", "Oldest published"), ("title", "Title A-Z")])
    status = forms.ChoiceField(required=False, choices=[("", "All public records"), ("public_draft", "Public drafts"), ("planned", "Planned briefs"), ("under_review", "Under review"), ("version_of_record", "Versions of record")])
    page = forms.IntegerField(required=False, min_value=1, max_value=10000, widget=forms.HiddenInput())
    def clean(self):
        data = super().clean()
        for start, end in [("published_from", "published_to"), ("historical_from", "historical_to")]:
            if data.get(start) is not None and data.get(end) is not None and data[start] > data[end]:
                raise forms.ValidationError("A range's start must not follow its end.")
        return data
