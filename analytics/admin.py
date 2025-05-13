from django.contrib import admin

from admin_management.models import ReportLog


@admin.register(ReportLog)
class ReportLogAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'generated_at', 'user')
    list_filter = ('report_type', 'generated_at')
    search_fields = ('report_type',)