4.0 Grading Standard LTI App
===========================

A Django LTI Application for creating grading standards and adding them to a Canvas course

Installation
------------

**Project directory**

Install grading-standard-lti in your project.

    $ cd [project]
    $ pip install UW-Grading-Standard-LTI

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
