# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class ResearchField(models.Model):
    code = models.CharField("编号", max_length=20, unique=True)
    name = models.CharField("名称", max_length=100)
    is_active = models.BooleanField("是否激活", default=True)

    class Meta:
        verbose_name = "研究领域"
        verbose_name_plural = "研究领域"

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField("姓名", max_length=50)
    institution = models.CharField("单位", max_length=200)
    title = models.CharField("职称", max_length=50, blank=True)
    email = models.EmailField("电子邮箱", unique=True)
    phone = models.CharField(
        "电话", max_length=20, validators=[RegexValidator(r'^\+?\d{10,15}$', "电话格式无效")])
    orcid = models.CharField("ORCID", max_length=50, blank=True)
    research_fields = models.ManyToManyField(ResearchField, verbose_name="研究领域")

    class Meta:
        verbose_name = "用户资料"
        verbose_name_plural = "用户资料"

    def __str__(self):
        return self.full_name

class Role(models.Model):
    name = models.CharField("角色名称", max_length=20, unique=True)
    description = models.CharField("描述", max_length=100)

    class Meta:
        verbose_name = "角色"
        verbose_name_plural = "角色"

    def __str__(self):
        return self.name

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    is_active = models.BooleanField("是否激活", default=True)

    class Meta:
        unique_together = ('user', 'role')
        verbose_name = "用户角色"
        verbose_name_plural = "用户角色"

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"