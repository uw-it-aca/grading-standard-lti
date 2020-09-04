from .base_settings import *

DEBUG = True if (os.getenv('ENV', 'localdev') == 'localdev') else False

INSTALLED_APPS += [
    'grading_standard.apps.GradingStandardConfig',
    'grade_conversion_calculator',
    'compressor',
]

COMPRESS_ROOT = '/static/'
COMPRESS_PRECOMPILERS = (('text/less', 'lessc {infile} {outfile}'),)
COMPRESS_OFFLINE = True
STATICFILES_FINDERS += ('compressor.finders.CompressorFinder',)


