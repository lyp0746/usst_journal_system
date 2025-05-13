# manuscripts/admin.py
from django.contrib import admin
from .models import Manuscript, ManuscriptType

@admin.register(ManuscriptType)
class ManuscriptTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'verbose_name', 'is_active')
    search_fields = ('name', 'verbose_name')

@admin.register(Manuscript)
class ManuscriptAdmin(admin.ModelAdmin):
    list_display = ('manuscript_id', 'title_cn', 'status', 'submitter', 'submit_date')
    list_filter = ('status', 'type', 'research_field')
    search_fields = ('manuscript_id', 'title_cn', 'title_en')
    date_hierarchy = 'submit_date'