# review_process/models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.utils import timezone

from accounts.models import ResearchField
from notifications.models import Notification


class ReviewerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="reviewer_profile")
    expertise = models.TextField("专业领域", blank=True)
    max_reviews_per_month = models.IntegerField(
        "每月最大审稿量", default=5, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    research_fields = models.ManyToManyField(ResearchField, verbose_name="研究领域")
    is_active = models.BooleanField("是否激活", default=True)

    class Meta:
        verbose_name = "审稿人资料"
        verbose_name_plural = "审稿人资料"

    def __str__(self):
        return self.user.username

    def get_current_month_reviews(self):
        """获取当前月份的活跃审稿任务数"""
        current_year = timezone.now().year
        current_month = timezone.now().month
        return self.user.review_assignments.filter(
            invited_date__year=current_year,
            invited_date__month=current_month,
            status__in=['INVITED', 'ACCEPTED', 'IN_PROGRESS']
        ).count()

    def get_quality_score(self):
        """计算历史审稿质量评分"""
        scores = ReviewForm.objects.filter(
            assignment__reviewer=self.user
        ).aggregate(
            avg=Avg('originality_score') + Avg('technical_score') + Avg('presentation_score')
        )['avg'] or 0
        return scores / 3

    def has_conflict(self, manuscript):
        """检查利益冲突"""
        return self.user.profile.institution == manuscript.submitter.profile.institution

from manuscripts.models import Manuscript

class ReviewAssignment(models.Model):
    manuscript = models.ForeignKey(Manuscript, on_delete=models.CASCADE, related_name="review_assignments")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="review_assignments")
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_reviews")
    STATUS_CHOICES = [
        ('INVITED', '已邀请'),
        ('ACCEPTED', '已接受'),
        ('DECLINED', '已拒绝'),
        ('IN_PROGRESS', '审稿中'),
        ('COMPLETED', '已完成'),
    ]
    status = models.CharField("状态", max_length=20, choices=STATUS_CHOICES, default='INVITED')
    invited_date = models.DateTimeField("邀请日期", auto_now_add=True)
    response_date = models.DateTimeField("响应日期", null=True, blank=True)
    due_date = models.DateTimeField("截止日期", null=True, blank=True)
    completion_date = models.DateTimeField("完成日期", null=True, blank=True)
    decline_reason = models.TextField("拒绝原因", blank=True)

    class Meta:
        verbose_name = "审稿任务"
        verbose_name_plural = "审稿任务"
        unique_together = ('manuscript', 'reviewer')  # 防止重复分配

    def __str__(self):
        return f"{self.reviewer.username} - {self.manuscript.manuscript_id}"

    def clean(self):
        if ReviewAssignment.objects.filter(
                manuscript=self.manuscript, reviewer=self.reviewer
        ).exclude(id=self.id).exists():
            raise ValidationError("该审稿人已分配给此稿件")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == 'COMPLETED':
            # 检查所有审稿任务是否完成
            manuscript = self.manuscript
            all_completed = all(
                assignment.status == 'COMPLETED'
                for assignment in manuscript.review_assignments.all()
            )
            if all_completed and manuscript.status == 'UNDER_REVIEW':
                # 更新稿件状态为 REVISION_REQUIRED
                manuscript.status = 'REVISION_REQUIRED'
                manuscript.save()
                # 通知编辑
                editor = manuscript.handling_editor
                if editor:
                    Notification.objects.create(
                        recipient=editor,
                        notification_type='DECISION',
                        title=f"稿件 {manuscript.manuscript_id} 外审完成",
                        message=f"请审阅稿件 {manuscript.manuscript_id} 的外审意见并作出决定。",
                        url=f"/editor/review_summary/{manuscript.manuscript_id}/",
                        related_id=manuscript.manuscript_id
                    )

class ReviewForm(models.Model):
    assignment = models.OneToOneField(ReviewAssignment, on_delete=models.CASCADE, related_name="review_form")
    originality_score = models.IntegerField(
        "原创性评分", null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    technical_score = models.IntegerField(
        "技术水平评分", null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    presentation_score = models.IntegerField(
        "表达清晰度评分", null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comments_to_author = models.TextField("给作者的评语", blank=True)
    comments_to_editor = models.TextField("给编辑的评语", blank=True)
    DECISION_CHOICES = [
        ('ACCEPT', '接受'),
        ('MINOR_REVISION', '小修后接受'),
        ('REJECT', '拒绝'),
    ]
    decision = models.CharField("建议决定", max_length=20, choices=DECISION_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "评审表"
        verbose_name_plural = "评审表"

    def __str__(self):
        return f"Review for {self.assignment.manuscript.manuscript_id}"