from .base_settings import *
import os

if os.getenv('ENV', 'localdev') == 'localdev':
    DEBUG = True

INSTALLED_APPS += [
    'grading_standard.apps.GradingStandardConfig',
    'grade_conversion_calculator',
    'compressor',
    'django_extensions',
]

if os.getenv('ENV', 'localdev') != 'localdev':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '172.18.0.28',
            'PORT': '3306',
            'NAME': 'grading_standards_test',
            'USER': os.getenv('DATABASE_USERNAME', None),
            'PASSWORD': os.getenv('DATABASE_PASSWORD', None),
        },
        'postgres': {
            'ENGINE': 'django.db.backends.postgresql',
            'HOST': '172.18.1.43',
            'PORT': '5432',
            'NAME': 'grading_standards_test',
            'USER': os.getenv('DATABASE_USERNAME', None),
            'PASSWORD': os.getenv('DATABASE_PASSWORD', None),
        },
    }


COMPRESS_ROOT = '/static/'
COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)
COMPRESS_OFFLINE = True

STATICFILES_FINDERS += (
    'compressor.finders.CompressorFinder',
)

DOCUMENTATION_URL = os.getenv('DOCUMENTATION_URL')
