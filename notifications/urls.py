from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.notification_list, name='notification_list'),
    path('mark_read/', views.mark_read, name='mark_read'),
]