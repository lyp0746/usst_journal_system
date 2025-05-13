# usst_journal_system/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('manuscripts/', include('manuscripts.urls')),
    path('notifications/', include('notifications.urls')),
    path('review_process/', include('review_process.urls')),
    path('editor/', include('editor.urls')),
    path('publication/', include('publication.urls')),
    path('analytics/', include('analytics.urls')),
    path('admin_management/', include('admin_management.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)