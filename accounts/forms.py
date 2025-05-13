# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, ResearchField

class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(max_length=50, label="姓名")
    institution = forms.CharField(max_length=200, label="单位")
    title = forms.CharField(max_length=50, required=False, label="职称")
    email = forms.EmailField(label="电子邮箱")
    phone = forms.CharField(max_length=20, label="电话")
    orcid = forms.CharField(max_length=50, required=False, label="ORCID")
    research_fields = forms.ModelMultipleChoiceField(
        queryset=ResearchField.objects.filter(is_active=True), label="研究领域")

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'full_name', 'institution', 'title', 'email', 'phone', 'orcid', 'research_fields')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('full_name', 'institution', 'title', 'email', 'phone', 'orcid', 'research_fields')