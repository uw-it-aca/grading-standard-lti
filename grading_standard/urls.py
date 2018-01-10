from django.conf.urls import url
from grading_standard.views import LaunchView, GradingStandardView


urlpatterns = [
    url(r'^$', LaunchView.as_view()),
    url(r'^api/v1/grading_standards/$', GradingStandardView.as_view()),
    url(r'^api/v1/grading_standards/(?P<grading_standard_id>[^/]*)$',
        GradingStandardView.as_view()),
]
