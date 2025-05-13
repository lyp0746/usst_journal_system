# editor/forms.py
from django import forms
from manuscripts.models import Manuscript

class InitialReviewForm(forms.ModelForm):
    comment = forms.CharField(
        label="初审意见", widget=forms.Textarea(attrs={'rows': 4}), required=False
    )

    class Meta:
        model = Manuscript
        fields = ['status', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            ('UNDER_REVIEW', '通过初审'),
            ('REJECT_INITIAL', '初审拒绝'),
        ]

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        comment = cleaned_data.get('comment')
        if status == 'REJECT_INITIAL' and not comment:
            raise forms.ValidationError("初审拒绝需填写意见")
        if status == 'REJECT_INITIAL' and comment and len(comment) < 100:
            raise forms.ValidationError("初审意见需至少100字")
        return cleaned_data

from accounts.models import UserRole
from review_process.models import ReviewerProfile

class ReviewerAssignmentForm(forms.Form):
    reviewers = forms.ModelMultipleChoiceField(
        queryset=UserRole.objects.filter(role__name='Reviewer', is_active=True),
        widget=forms.CheckboxSelectMultiple,
        label="选择审稿人"
    )

    def clean_reviewers(self):
        reviewers = self.cleaned_data['reviewers']
        if len(reviewers) < 2 or len(reviewers) > 3:
            raise forms.ValidationError("请选择2-3位审稿人")
        return reviewers

class DecisionForm(forms.ModelForm):
    decision_comment = forms.CharField(
        label="编辑意见", widget=forms.Textarea(attrs={'rows': 4}), required=True
    )

    class Meta:
        model = Manuscript
        fields = ['status', 'decision_comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [
            ('ACCEPTED', '接受'),
            ('REVISION_REQUIRED', '需要修改'),
            ('REJECTED', '拒绝'),
        ]

    def clean_decision_comment(self):
        comment = self.cleaned_data['decision_comment']
        if len(comment) < 1 or len(comment) > 500:
            raise forms.ValidationError("编辑意见需100-500字")
        return comment