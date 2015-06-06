from django.conf.urls import patterns, url, include
from grading_standard.views import GradingStandard


urlpatterns = patterns(
    'grading_standard.views',
    url(r'^$', 'Main'),
    url(r'^api/v1/grading_standards/$', GradingStandard().run),
    url(r'^api/v1/grading_standards/(?P<grading_standard_id>[^/]*)$',
        GradingStandard().run),
)
