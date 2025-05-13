# manuscripts/forms.py
import json

from django import forms
from django.utils import timezone

from .models import Manuscript, ManuscriptType
from accounts.models import ResearchField
import random


class ManuscriptSubmissionForm(forms.ModelForm):
    # 使用隐藏字段存储作者数据JSON
    authors_data = forms.CharField(widget=forms.HiddenInput(), required=False)
    manuscript_file = forms.FileField(label="论文全文", help_text="PDF、DOC 或 DOCX 文件，<50MB")
    additional_file = forms.FileField(label="补充材料", required=False, help_text="上传ZIP文件，选填")
    copyright_agreement = forms.BooleanField(label="著作权声明", required=True,
                                             help_text="我确认已阅读并同意著作权转让协议")

    # 添加一个隐藏字段来传递提交类型
    submission_type = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Manuscript
        fields = [
            'title_cn', 'title_en', 'type', 'research_field', 'category_number',
            'abstract_cn', 'abstract_en', 'keywords_cn', 'keywords_en',
            'authors_data', 'submission_type',
            'manuscript_file', 'additional_file', 'copyright_agreement'
        ]
        widgets = {
            'abstract_cn': forms.Textarea(attrs={'rows': 5}),
            'abstract_en': forms.Textarea(attrs={'rows': 5}),
            'keywords_cn': forms.TextInput(attrs={'placeholder': '用逗号分隔，如：人工智能,机器学习'}),
            'keywords_en': forms.TextInput(attrs={'placeholder': '用逗号分隔，如：AI,Machine Learning'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['type'].queryset = ManuscriptType.objects.filter(is_active=True)
        self.fields['research_field'].queryset = ResearchField.objects.filter(is_active=True)

        # 验证作者数据

    def clean(self):
        cleaned_data = super().clean()
        authors_data = cleaned_data.get('authors_data')

        try:
            if authors_data:
                authors_list = json.loads(authors_data)
                if not authors_list:
                    raise forms.ValidationError("至少需要一位作者")

                    # 验证是否有且仅有一位通讯作者
                corresponding_authors = [a for a in authors_list if a.get('is_corresponding')]
                if len(corresponding_authors) != 1:
                    raise forms.ValidationError("必须指定一位通讯作者")
            else:
                raise forms.ValidationError("请添加作者信息")
        except json.JSONDecodeError:
            raise forms.ValidationError("作者数据格式不正确")

        return cleaned_data

    def clean_title_cn(self):
        title = self.cleaned_data['title_cn']
        if len(title) > 200:
            raise forms.ValidationError("中文标题不得超过200字")
        return title

    def clean_abstract_cn(self):
        abstract = self.cleaned_data['abstract_cn']
        if len(abstract) < 1 or len(abstract) > 500:
            raise forms.ValidationError("中文摘要需200-500字")
        return abstract

    def clean_manuscript_file(self):
        file = self.cleaned_data.get('manuscript_file')
        if file:
            ext = file.name.lower().split('.')[-1]
            if ext not in ['pdf', 'doc', 'docx']:
                raise forms.ValidationError("仅支持 PDF、DOC 或 DOCX 文件")
            if file.size > 50 * 1024 * 1024:  # 50MB
                raise forms.ValidationError("文件大小不能超过 50MB")
        return file

    def clean_additional_file(self):
        file = self.cleaned_data.get('additional_file')
        if file:
            if not file.name.endswith('.zip'):
                raise forms.ValidationError("补充材料仅支持ZIP文件")
        return file

    def save(self, commit=True, user=None):
        manuscript = super().save(commit=False)

        # 处理作者数据
        authors_data = self.cleaned_data.get('authors_data')
        if authors_data:
            authors_list = json.loads(authors_data)
            # 存储作者信息的JSON字符串
            manuscript.authors_json = authors_data

            # 设置通讯作者
            for author in authors_list:
                if author.get('is_corresponding'):
                    manuscript.corresponding_author = author.get('name')
                    break

        if user:
            manuscript.submitter = user

            # 通过submission_type字段判断是否为正式提交
        submission_type = self.cleaned_data.get('submission_type')
        if submission_type == 'submit':
            manuscript.status = 'SUBMITTED'

            # 如果状态是提交状态，设置相似率和提交日期
        if manuscript.status == 'SUBMITTED':
            manuscript.similarity_rate = random.uniform(0, 30)
            manuscript.submit_date = timezone.now()
        elif not manuscript.status:  # 如果状态未设置，默认为草稿
            manuscript.status = 'DRAFT'

        if commit:
            manuscript.save()
            self.save_m2m()
        return manuscript

class ManuscriptRevisionForm(forms.ModelForm):
    revised_file = forms.FileField(label="修改稿", help_text="上传PDF文件，<50MB")
    revision_comments = forms.CharField(widget=forms.Textarea, label="修改说明", help_text="支持Markdown格式")

    class Meta:
        model = Manuscript
        fields = ['revised_file', 'revision_comments']

    def clean_revised_file(self):
        file = self.cleaned_data['revised_file']
        if not file.name.endswith('.pdf'):
            raise forms.ValidationError("仅支持PDF文件")
        if file.size > 50 * 1024 * 1024:
            raise forms.ValidationError("文件大小不得超过50MB")
        return file

from django import forms
from .models import Manuscript, ResearchField

class ManuscriptSearchForm(forms.Form):
    keyword = forms.CharField(required=False, label="关键词", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '标题或编号'}))
    status = forms.ChoiceField(
        choices=[('', '全部状态')] + Manuscript.STATUS_CHOICES,
        required=False,
        label="状态",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    research_field = forms.ModelChoiceField(
        queryset=ResearchField.objects.filter(is_active=True),
        required=False,
        label="研究领域",
        empty_label="全部领域",
        widget=forms.Select(attrs={'class': 'form-select'})
    )