# review_process/admin.py
from django.contrib import admin
from .models import ReviewerProfile, ReviewAssignment, ReviewForm

@admin.register(ReviewerProfile)
class ReviewerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'max_reviews_per_month', 'is_active')
    search_fields = ('user__username', 'expertise')
    filter_horizontal = ('research_fields',)

@admin.register(ReviewAssignment)
class ReviewAssignmentAdmin(admin.ModelAdmin):
    list_display = ('manuscript', 'reviewer', 'status', 'invited_date', 'due_date')
    list_filter = ('status',)
    search_fields = ('manuscript__manuscript_id', 'reviewer__username')

@admin.register(ReviewForm)
class ReviewFormAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'originality_score', 'technical_score', 'presentation_score', 'decision')
    list_filter = ('decision',)
    search_fields = ('assignment__manuscript__manuscript_id',)