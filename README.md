# 4.0 Grading Standard LTI App

[![Build Status](https://github.com/uw-it-aca/grading-standard-lti/workflows/Build%2C%20Test%20and%20Deploy/badge.svg?branch=master)](https://github.com/uw-it-aca/grading-standard-lti/actions)
[![Coverage Status](https://coveralls.io/repos/github/uw-it-aca/grading-standard-lti/badge.svg?branch=master)](https://coveralls.io/github/uw-it-aca/grading-standard-lti?branch=master)

A Django LTI Application for creating grading standards and adding them to a Canvas course

Project settings.py
------------------

**INSTALLED_APPS**

    'grading_standard',
    'grade_conversion_calculator',
    'blti',

**REST client app settings**

    RESTCLIENTS_CANVAS_DAO_CLASS = 'Live'
    RESTCLIENTS_CANVAS_HOST = 'example.instructure.com'
    RESTCLIENTS_CANVAS_OAUTH_BEARER = '...'

**BLTI settings**

[django-blti settings](https://github.com/uw-it-aca/django-blti#project-settingspy)

Project urls.py
---------------
    url(r'^grading_standard/', include('grading_standard.urls')),
