from .base_settings import *
import os

if os.getenv('ENV', 'localdev') == 'localdev':
    DEBUG = True

INSTALLED_APPS += [
    'grading_standard.apps.GradingStandardConfig',
    'grade_conversion_calculator',
    'compressor',
]

DEFAULT_AUTO_FIELD='django.db.models.AutoField'

COMPRESS_ROOT = '/static/'
COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)
COMPRESS_OFFLINE = True

STATICFILES_FINDERS += (
    'compressor.finders.CompressorFinder',
)

DOCUMENTATION_URL = os.getenv('DOCUMENTATION_URL')
