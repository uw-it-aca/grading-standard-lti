from django.conf.urls import patterns, url, include
from grading_standard.views import LaunchView, GradingStandardView


urlpatterns = patterns(
    '',
    url(r'^$', LaunchView.as_view()),
    url(r'^api/v1/grading_standards/$', GradingStandardView().run),
    url(r'^api/v1/grading_standards/(?P<grading_standard_id>[^/]*)$',
        GradingStandardView().run),
)
