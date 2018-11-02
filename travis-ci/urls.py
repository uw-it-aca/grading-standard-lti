from django.urls import include, re_path

urlpatterns = [
    re_path(r'^grading_standard/', include('grading_standard.urls')),
]
