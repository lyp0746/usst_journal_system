# manuscripts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('submission/', views.submission, name='manuscript_submission'),
    path('list/', views.manuscript_list, name='manuscript_list'),
    path('detail/<str:manuscript_id>/', views.manuscript_detail, name='manuscript_detail'),
    path('revise/<str:manuscript_id>/', views.revise_manuscript, name='manuscript_revise'),
    path('withdraw/<str:manuscript_id>/', views.withdraw_manuscript, name='manuscript_withdraw'),
    path('guidelines/', views.guidelines, name='guidelines'),
    path('download-template/', views.download_template, name='download_template'),
    path('file/<str:manuscript_id>/', views.ManuscriptFileDownloadView.as_view(), name='manuscript_file_download'),
]