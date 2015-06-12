from django.conf.urls import patterns, include, url
from django.contrib import admin


urlpatterns = patterns('',
    url(r'^grading_standard/', include('grading_standard.urls')),
)
