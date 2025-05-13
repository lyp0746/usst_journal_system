from django.db import models
from manuscripts.models import Manuscript

class Volume(models.Model):
    volume_number = models.IntegerField("卷号", unique=True)
    year = models.IntegerField("年份")
    is_published = models.BooleanField("是否发布", default=False)
    publish_date = models.DateField("发布日期", null=True, blank=True)

    class Meta:
        verbose_name = "卷"
        verbose_name_plural = "卷"

    def __str__(self):
        return f"Volume {self.volume_number} ({self.year})"

class Issue(models.Model):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE, related_name="issues", verbose_name="卷")
    issue_number = models.IntegerField("期号")
    publication_date = models.DateField("出版日期", null=True, blank=True)
    is_published = models.BooleanField("是否发布", default=False)

    class Meta:
        unique_together = ('volume', 'issue_number')
        verbose_name = "期"
        verbose_name_plural = "期"

    def __str__(self):
        return f"Issue {self.issue_number} of Volume {self.volume.volume_number}"

class ManuscriptPublication(models.Model):
    manuscript = models.OneToOneField(Manuscript, on_delete=models.CASCADE, verbose_name="稿件")
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="manuscripts", verbose_name="期")
    page_start = models.IntegerField("起始页码", null=True, blank=True)
    page_end = models.IntegerField("结束页码", null=True, blank=True)
    doi = models.CharField("DOI", max_length=100, blank=True)
    publication_date = models.DateField("出版日期", null=True, blank=True)

    class Meta:
        verbose_name = "稿件出版"
        verbose_name_plural = "稿件出版"

    def __str__(self):
        return f"{self.manuscript.manuscript_id} in {self.issue}"