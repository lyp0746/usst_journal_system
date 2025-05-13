from django.contrib.auth.models import User
from django.db import models


# 报表日志
class ReportLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="操作用户")
    report_type = models.CharField("报表类型", max_length=50)
    generated_at = models.DateTimeField("生成时间", auto_now_add=True)
    file_path = models.FileField("报表文件", upload_to="reports/", blank=True)

    class Meta:
        verbose_name = "报表日志"
        verbose_name_plural = "报表日志"

    def __str__(self):
        return f"{self.report_type} - {self.generated_at}"

# 系统设置
class SystemSetting(models.Model):
    key = models.CharField("键", max_length=100, unique=True)
    value = models.TextField("值")
    description = models.TextField("描述", blank=True)

    class Meta:
        verbose_name = "系统设置"
        verbose_name_plural = "系统设置"

    def __str__(self):
        return self.key

# 系统日志
class SystemLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, verbose_name="操作用户")
    action = models.CharField("操作", max_length=200)
    timestamp = models.DateTimeField("时间", auto_now_add=True)
    details = models.TextField("详情", blank=True)
    is_error = models.BooleanField("是否错误", default=False)

    class Meta:
        verbose_name = "系统日志"
        verbose_name_plural = "系统日志"

    def __str__(self):
        return f"{self.action} - {self.timestamp}"
