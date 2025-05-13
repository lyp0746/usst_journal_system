import random

from django.db import models
from django.contrib.auth.models import User  
from django.core.validators import MinValueValidator, MaxValueValidator  
from django.core.exceptions import ValidationError  
from django.utils import timezone  
from accounts.models import ResearchField  

class ManuscriptType(models.Model):  
    name = models.CharField("类型名称", max_length=50, unique=True)  
    verbose_name = models.CharField("显示名称", max_length=100)  
    is_active = models.BooleanField("是否激活", default=True)  

    class Meta:  
        verbose_name = "稿件类型"  
        verbose_name_plural = "稿件类型"  

    def __str__(self):  
        return self.verbose_name  

class Manuscript(models.Model):  
    manuscript_id = models.CharField("稿件编号", max_length=20, unique=True)  
    STATUS_CHOICES = [  
        ('DRAFT', '草稿'),  
        ('SUBMITTED', '已提交'),  
        ('UNDER_REVIEW', '外审中'),  
        ('REVISION_REQUIRED', '需要修改'),  
        ('REVISED', '已修改'),  
        ('ACCEPTED', '已接受'),  
        ('REJECTED', '已拒绝'),  
        ('REJECT_INITIAL', '初审拒绝'),  
        ('PUBLISHED', '已发表'),  
    ]  
    STATUS_CHOICES_DICT = dict(STATUS_CHOICES)  
    status = models.CharField("状态", max_length=30, choices=STATUS_CHOICES, default='DRAFT')  
    title_cn = models.CharField("中文标题", max_length=200)  
    title_en = models.CharField("英文标题", max_length=200)  
    authors = models.TextField("作者列表")  
    affiliations = models.TextField("作者单位")  
    corresponding_author = models.CharField("通讯作者", max_length=100)  
    submitter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submitted_manuscripts")  
    type = models.ForeignKey(ManuscriptType, on_delete=models.SET_NULL, null=True, verbose_name="稿件类型")  
    abstract_cn = models.TextField("中文摘要")  
    abstract_en = models.TextField("英文摘要")  
    keywords_cn = models.CharField("中文关键词", max_length=200)  
    keywords_en = models.CharField("英文关键词", max_length=200)  
    category_number = models.CharField("中图分类号", max_length=50, blank=True)  
    research_field = models.ForeignKey(ResearchField, on_delete=models.SET_NULL, null=True, verbose_name="研究领域")  
    similarity_rate = models.FloatField(  
        "查重率", default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])  
    manuscript_file = models.FileField("原稿文件", upload_to="manuscripts/")  
    revised_file = models.FileField("修改稿文件", upload_to="manuscripts/revised/", blank=True)  
    additional_file = models.FileField("附加文件", upload_to="manuscripts/additional/", blank=True)  
    created_at = models.DateTimeField("创建时间", auto_now_add=True)  
    updated_at = models.DateTimeField("更新时间", auto_now=True)  
    submit_date = models.DateTimeField("提交时间", null=True, blank=True)  
    handling_editor = models.ForeignKey(  
        User, on_delete=models.SET_NULL, related_name="handling_manuscripts", null=True, blank=True, verbose_name="责任编辑"  
    )  
    decision_date = models.DateTimeField("决定时间", null=True, blank=True)  
    publish_date = models.DateField("出版日期", null=True, blank=True)  
    volume = models.IntegerField("卷号", null=True, blank=True)  
    issue = models.IntegerField("期号", null=True, blank=True)  

    class Meta:  
        verbose_name = "稿件"  
        verbose_name_plural = "稿件"  

    def save(self, *args, **kwargs):  
        if not self.manuscript_id:  
            year = timezone.now().year  
            count = Manuscript.objects.filter(manuscript_id__startswith=f'MS{year}').count() + 1  
            self.manuscript_id = f'MS{year}{count:04d}'  
        if self.pk:  
            old_instance = Manuscript.objects.get(pk=self.pk)  
            self.validate_status_transition(old_instance.status, self.status)
            # 修复：状态变为 SUBMITTED 时生成随机查重率
            if old_instance.status == 'DRAFT' and self.status == 'SUBMITTED' and self.similarity_rate == 0.0:
                self.similarity_rate = round(random.uniform(0.0, 30.0), 2)
        super().save(*args, **kwargs)  

    def validate_status_transition(self, current_status, new_status):  
        VALID_TRANSITIONS = {  
            'DRAFT': ['SUBMITTED','DRAFT'],
            'SUBMITTED': ['UNDER_REVIEW', 'REJECT_INITIAL', 'REJECTED','SUBMITTED'],
            'UNDER_REVIEW': ['REVISION_REQUIRED', 'ACCEPTED', 'REJECTED','UNDER_REVIEW'],
            'REVISION_REQUIRED': ['REVISED', 'ACCEPTED', 'REJECTED','REVISION_REQUIRED'],
            'REVISED': ['UNDER_REVIEW', 'ACCEPTED', 'REJECTED', 'REVISED'],
            'ACCEPTED': ['PUBLISHED','ACCEPTED'],
            'REJECTED': ['REJECTED'],
            'REJECT_INITIAL': [],  
            'PUBLISHED': ['PUBLISHED'],
        }  
        if new_status not in VALID_TRANSITIONS.get(current_status, []):  
            raise ValidationError(f"无效的状态转换：{current_status} -> {new_status}")  

    def __str__(self):  
        return self.manuscript_id

class ManuscriptRevision(models.Model):
    manuscript = models.ForeignKey('Manuscript', on_delete=models.CASCADE, related_name="revisions")
    version = models.IntegerField("版本号")
    revised_file = models.FileField("修改稿文件", upload_to="manuscripts/revised/")
    comments = models.TextField("修改说明", blank=True)
    submitted_at = models.DateTimeField("提交时间", auto_now_add=True)

    class Meta:
        unique_together = ('manuscript', 'version')
        verbose_name = "稿件修改版本"
        verbose_name_plural = "稿件修改版本"

    def __str__(self):
        return f"{self.manuscript.manuscript_id} - v{self.version}"