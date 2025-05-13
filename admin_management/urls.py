from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='admin_dashboard'),
    path('settings/', views.settings, name='admin_settings'),
    path('research_fields/', views.research_fields, name='research_fields'),
    path('error_logs/', views.error_logs, name='error_logs'),
    path('backup/', views.backup, name='backup'),
    path('user_audit/', views.UserAuditView.as_view(), name='user_audit'),
    path('user_management/', views.UserManagementView.as_view(), name='user_management'),
    path('user_edit/<int:user_id>/', views.UserEditView.as_view(), name='user_edit'),
]