from django.urls import path
from . import views

urlpatterns = [
    path('volumes/', views.volume_list, name='volume_list'),
    path('volumes/<int:volume_id>/issues/create/', views.issue_create, name='issue_create'),
    path('volumes/<int:volume_id>/issues/<int:issue_id>/arrange/', views.arrange_manuscripts, name='arrange_manuscripts'),
    path('volumes/<int:volume_id>/issues/<int:issue_id>/toc/', views.generate_toc, name='generate_toc'),
]