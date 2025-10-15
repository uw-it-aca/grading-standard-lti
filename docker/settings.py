from .base_settings import *
import os

if os.getenv('ENV', 'localdev') == 'localdev':
    DEBUG = True
else:
    CSRF_TRUSTED_ORIGINS = ['https://' + os.getenv('CLUSTER_CNAME')]

INSTALLED_APPS += [
    'grading_standard.apps.GradingStandardConfig',
    'grade_conversion_calculator',
    'compressor',
]

COMPRESS_ROOT = '/static/'
COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)
COMPRESS_OFFLINE = True

STATICFILES_FINDERS += (
    'compressor.finders.CompressorFinder',
)

RESTCLIENTS_CANVAS_USER_AGENT = 'UW-GradingStandard-LTI/0.1'
DOCUMENTATION_URL = os.getenv('DOCUMENTATION_URL')
