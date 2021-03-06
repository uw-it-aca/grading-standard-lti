import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/grading-standard-lti>`_.
"""

version_path = 'grading_standard/VERSION'
VERSION = open(os.path.join(os.path.dirname(__file__), version_path)).read()
VERSION = VERSION.replace("\n", "")

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='UW-Grading-Standard-LTI',
    version=VERSION,
    packages=['grading_standard'],
    include_package_data=True,
    install_requires = [
        'Django~=2.2',
        'django-blti~=2.2',
        'django-compressor',
        'UW-RestClients-Core~=1.3',
        'UW-RestClients-Canvas~=1.1',
        'UW-Grade-Conversion-Calculator>=1.1',
    ],
    license='Apache License, Version 2.0',
    description=(
        'An LTI app for creating grading standards and adding them to a '
        'Canvas course'),
    long_description=README,
    url='https://github.com/uw-it-aca/grading-standard-lti',
    author="UW-IT AXDD",
    author_email="aca-it@uw.edu",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
    ],
)
