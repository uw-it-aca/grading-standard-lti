# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.urls import re_path
from django.views.i18n import JavaScriptCatalog
from grading_standard.views import LaunchView, GradingStandardView

urlpatterns = [
    re_path(r'^$', LaunchView.as_view(), name="lti-launch"),
    re_path(r'^api/v1/grading_standards/$', GradingStandardView.as_view()),
    re_path(r'^api/v1/grading_standards/(?P<grading_standard_id>[^/]*)$',
            GradingStandardView.as_view()),
    re_path(r'^jsi18n/$', JavaScriptCatalog.as_view(
            packages=['grade_conversion_calculator', 'grading_standard']),
            name='javascript-catalog')
]
