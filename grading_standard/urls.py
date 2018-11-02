from django.urls import re_path
from grading_standard.views import LaunchView, GradingStandardView

urlpatterns = [
    re_path(r'^$', LaunchView.as_view()),
    re_path(r'^api/v1/grading_standards/$', GradingStandardView.as_view()),
    re_path(r'^api/v1/grading_standards/(?P<grading_standard_id>[^/]*)$',
            GradingStandardView.as_view()),
]
