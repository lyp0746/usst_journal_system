# notifications/admin.py
from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'message')
    date_hierarchy = 'created_at'