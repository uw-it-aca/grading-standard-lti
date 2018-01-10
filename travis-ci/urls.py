from django.conf.urls import include, url


urlpatterns = [
    url(r'^grading_standard/', include('grading_standard.urls')),
]
