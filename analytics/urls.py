from django.urls import path
from . import views
from .views import ReportGenerateView

urlpatterns = [
    path('report_generate/', ReportGenerateView.as_view(), name='report_generate'),
]