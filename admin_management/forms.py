from django import forms

from accounts.models import ResearchField, UserRole
from .models import SystemSetting


class SystemSettingForm(forms.ModelForm):
    class Meta:
        model = SystemSetting
        fields = ['key', 'value', 'description']
        widgets = {
            'value': forms.Textarea(attrs={'rows': 4}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ResearchFieldForm(forms.ModelForm):
    class Meta:
        model = ResearchField
        fields = ['code', 'name', 'is_active']


from django import forms
from django.contrib.auth.models import User
from accounts.models import UserProfile, Role

class UserEditForm(forms.ModelForm):
    full_name = forms.CharField(label="姓名", max_length=50)
    institution = forms.CharField(label="单位", max_length=200)
    title = forms.CharField(label="职称", max_length=50, required=False)
    email = forms.EmailField(label="电子邮箱")
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(), label="角色", widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            profile = self.instance.profile
            self.fields['full_name'].initial = profile.full_name
            self.fields['institution'].initial = profile.institution
            self.fields['title'].initial = profile.title
            self.fields['email'].initial = profile.email
            self.fields['roles'].initial = self.instance.roles.filter(is_active=True).values_list('role', flat=True)

    def save(self, *args, **kwargs):
        user = super().save(*args, **kwargs)
        profile = user.profile
        profile.full_name = self.cleaned_data['full_name']
        profile.institution = self.cleaned_data['institution']
        profile.title = self.cleaned_data['title']
        profile.email = self.cleaned_data['email']
        profile.save()
        UserRole.objects.filter(user=user).delete()
        for role in self.cleaned_data['roles']:
            UserRole.objects.create(user=user, role=role, is_active=True)
        return user