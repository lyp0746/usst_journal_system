# editor/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.editor_dashboard, name='editor_dashboard'),
    path('initial-review/<str:manuscript_id>/', views.initial_review, name='initial_review'),
    path('assign-reviewer/<str:manuscript_id>/', views.assign_reviewer, name='assign_reviewer'),
    path('progress-monitor/<str:manuscript_id>/', views.progress_monitor, name='progress_monitor'),
    path('replace-reviewer/<int:assignment_id>/', views.replace_reviewer, name='replace_reviewer'),
    path('review-summary/<str:manuscript_id>/', views.review_summary, name='review_summary'),
    path('decision/<str:manuscript_id>/', views.decision_form, name='decision_form'),
]