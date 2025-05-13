# review_process/forms.py
from django import forms
from django.contrib.auth.models import User

from .models import ReviewerProfile, ReviewForm
from accounts.models import ResearchField

class ReviewerProfileForm(forms.ModelForm):
    class Meta:
        model = ReviewerProfile
        fields = ['expertise', 'max_reviews_per_month', 'research_fields']
        widgets = {
            'expertise': forms.Textarea(attrs={'rows': 4}),
            'research_fields': forms.CheckboxSelectMultiple(),
            'max_reviews_per_month': forms.Select(choices=[(i, i) for i in range(1, 6)]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['research_fields'].queryset = ResearchField.objects.filter(is_active=True)

class ReviewInvitationResponseForm(forms.Form):
    response = forms.ChoiceField(
        label="响应", choices=[('ACCEPT', '接受'), ('DECLINE', '拒绝')], widget=forms.RadioSelect
    )
    decline_reason = forms.CharField(
        label="拒绝理由", widget=forms.Textarea(attrs={'rows': 4}), required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        response = cleaned_data.get('response')
        decline_reason = cleaned_data.get('decline_reason')
        if response == 'DECLINE' and not decline_reason:
            raise forms.ValidationError("请填写拒绝理由")
        if response == 'DECLINE' and (len(decline_reason) < 100 or len(decline_reason) > 300):
            raise forms.ValidationError("拒绝理由需100-300字")
        return cleaned_data

class ReviewFormForm(forms.ModelForm):
    class Meta:
        model = ReviewForm
        fields = [
            'originality_score', 'technical_score', 'presentation_score',
            'comments_to_author', 'comments_to_editor', 'decision'
        ]
        widgets = {
            'originality_score': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'technical_score': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'presentation_score': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'comments_to_author': forms.Textarea(attrs={'rows': 6}),
            'comments_to_editor': forms.Textarea(attrs={'rows': 4}),
            'decision': forms.Select(choices=ReviewForm.DECISION_CHOICES),
        }

    def clean_comments_to_author(self):
        comments = self.cleaned_data['comments_to_author']
        if self.cleaned_data.get('decision') and not comments:
            raise forms.ValidationError("评语不能为空")
        if comments and (len(comments) < 300 or len(comments) > 1000):
            raise forms.ValidationError("给作者的评语需300-1000字")
        return comments

    def clean_comments_to_editor(self):
        comments = self.cleaned_data['comments_to_editor']
        if self.cleaned_data.get('decision') and not comments:
            raise forms.ValidationError("评语不能为空")
        if comments and (len(comments) < 100 or len(comments) > 500):
            raise forms.ValidationError("给编辑的评语需100-500字")
        return comments

class ReviewerSelectForm(forms.Form):
    reviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(
            roles__role__name='Reviewer',
            reviewer_profile__is_active=True
        ),
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label="选择审稿人"
    )

    def __init__(self, *args, manuscript=None, **kwargs):
        super().__init__(*args, **kwargs)
        if manuscript:
            # 排除已分配的审稿人
            assigned_reviewers = manuscript.review_assignments.values_list('reviewer', flat=True)
            self.fields['reviewers'].queryset = self.fields['reviewers'].queryset.exclude(
                id__in=assigned_reviewers
            )