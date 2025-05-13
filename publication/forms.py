from django import forms
from .models import Volume, Issue, ManuscriptPublication
from manuscripts.models import Manuscript
from django.core.exceptions import ValidationError

class VolumeForm(forms.ModelForm):
    class Meta:
        model = Volume
        fields = ['volume_number', 'year', 'publish_date']
        widgets = {
            'publish_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        volume_number = cleaned_data.get('volume_number')
        year = cleaned_data.get('year')
        if volume_number and year and volume_number != year:
            raise ValidationError("卷号必须与年份一致")
        return cleaned_data

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['volume', 'issue_number', 'publication_date']
        widgets = {
            'publication_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_issue_number(self):
        issue_number = self.cleaned_data['issue_number']
        if not 1 <= issue_number <= 4:
            raise ValidationError("期号必须在1到4之间")
        return issue_number

class ManuscriptPublicationForm(forms.ModelForm):
    manuscript = forms.ModelChoiceField(
        queryset=Manuscript.objects.filter(status='ACCEPTED'),
        label="稿件"
    )

    class Meta:
        model = ManuscriptPublication
        fields = ['manuscript', 'issue', 'page_start', 'page_end', 'publication_date']
        widgets = {
            'publication_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        page_start = cleaned_data.get('page_start')
        page_end = cleaned_data.get('page_end')
        if page_start and page_end and page_end <= page_start:
            raise ValidationError("结束页码必须大于起始页码")
        return cleaned_data