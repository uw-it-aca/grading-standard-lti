from .base_urls import *
from django.conf.urls import include
from django.urls import re_path

urlpatterns += [
    re_path(r'^', include('grading_standard.urls')),
    re_path(r'^blti/', include('blti.urls')),
]
