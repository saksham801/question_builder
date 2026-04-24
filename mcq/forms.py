import json
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Question, Test


class PDFUploadForm(forms.Form):
    subject = forms.CharField(max_length=180, label='Subject', widget=forms.TextInput(attrs={'placeholder': 'e.g. Mathematics'}))
    topic = forms.CharField(max_length=190, label='Topic', widget=forms.TextInput(attrs={'placeholder': 'e.g. Algebra'}))
    pdf_file = forms.FileField(label='PDF File')

    def clean_pdf_file(self):
        pdf_file = self.cleaned_data.get('pdf_file')
        if pdf_file:
            if pdf_file.content_type not in ['application/pdf']:
                raise ValidationError(_('Only PDF files are allowed.'))
            if pdf_file.size > 50 * 1024 * 1024:
                raise ValidationError(_('File size must be under 50 MB.'))
        return pdf_file


class SaveParsedQuestionsForm(forms.Form):
    parsed_json = forms.CharField(widget=forms.HiddenInput())

    def clean_parsed_json(self):
        raw = self.cleaned_data.get('parsed_json', '')
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            raise ValidationError(_('Unable to parse the edited question payload.'))

        if not isinstance(parsed, list):
            raise ValidationError(_('Submitted data must be a list of questions.'))

        return parsed


class TestCreateForm(forms.Form):
    title = forms.CharField(max_length=250, label='Test Title')
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    duration_minutes = forms.IntegerField(min_value=1, initial=60, label='Duration (minutes)')
    total_marks = forms.IntegerField(min_value=1, initial=100, label='Total Marks')
    question_ids = forms.ModelMultipleChoiceField(
        queryset=Question.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Select Questions',
    )

    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions', None)
        super().__init__(*args, **kwargs)
        if questions is not None:
            self.fields['question_ids'].queryset = questions
