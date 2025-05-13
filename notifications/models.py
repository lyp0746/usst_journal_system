# notifications/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    TYPE_CHOICES = [
        ('SUBMISSION', '投稿通知'),
        ('REVIEW_INVITE', '审稿邀请'),
        ('REVIEW_REMINDER', '审稿提醒'),
        ('DECISION', '编辑决定'),
        ('REVISION', '修改要求'),
        ('ACCEPT', '录用通知'),
        ('REJECT', '退稿通知'),
        ('PUBLICATION', '出版通知'),
    ]
    notification_type = models.CharField("通知类型", max_length=20, choices=TYPE_CHOICES)
    title = models.CharField("标题", max_length=200)
    message = models.TextField("内容")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    is_read = models.BooleanField("是否已读", default=False)
    url = models.CharField("相关链接", max_length=200, blank=True)
    related_id = models.CharField("关联ID", max_length=50, blank=True)

    class Meta:
        verbose_name = "通知"
        verbose_name_plural = "通知"
        ordering = ['-created_at']

    def __str__(self):
        return self.title