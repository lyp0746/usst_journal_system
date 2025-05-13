# review_process/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('reviewer-profile/', views.reviewer_profile, name='reviewer_profile'),
    path('invitations/', views.invitation_list, name='invitation_list'),
    path('invitation/<int:assignment_id>/respond/', views.respond_invitation, name='respond_invitation'),
    path('manuscript/<str:manuscript_id>/view/', views.manuscript_view, name='manuscript_view'),
    path('review/<int:assignment_id>/form/', views.review_form, name='review_form'),
    path('review-history/', views.review_history, name='review_history'),
]