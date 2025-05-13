from django import forms
from .models import Notification


class NotificationSearchForm(forms.Form):
    keyword = forms.CharField(
        label="关键词搜索",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '搜索标题或内容'})
    )

    # 使用模型中的TYPE_CHOICES
    notification_type_choices = [('', '全部类型')] + Notification.TYPE_CHOICES

    notification_type = forms.ChoiceField(
        label="通知类型",
        choices=notification_type_choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    is_read = forms.ChoiceField(
        label="阅读状态",
        choices=[('', '全部状态'), ('True', '已读'), ('False', '未读')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )