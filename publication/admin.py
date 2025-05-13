from django.contrib import admin
from .models import Volume, Issue, ManuscriptPublication

@admin.register(Volume)
class VolumeAdmin(admin.ModelAdmin):
    list_display = ('volume_number', 'year', 'is_published', 'publish_date')
    list_filter = ('is_published',)
    search_fields = ('volume_number', 'year')

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('volume', 'issue_number', 'is_published', 'publication_date')
    list_filter = ('is_published', 'volume')
    search_fields = ('issue_number',)

@admin.register(ManuscriptPublication)
class ManuscriptPublicationAdmin(admin.ModelAdmin):
    list_display = ('manuscript', 'issue', 'page_start', 'page_end', 'doi')
    list_filter = ('issue',)
    search_fields = ('manuscript__manuscript_id', 'doi')