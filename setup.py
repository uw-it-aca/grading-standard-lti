#!/usr/bin/env python

import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='grading-standard-lti',
    version='1.0',
    packages=['grading_standard'],
    include_package_data=True,
    install_requires = [
        'setuptools',
        'django'
    ],
    license='Apache License, Version 2.0',  # example license
    description='An LTI app for creating grading standards and adding them to a Canvas course ',
    long_description=README,
    url='https://github.com/uw-it-aca/grading-standard-lti',
    author = "UW-IT ACA",
    author_email = "aca-it@uw.edu",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License', # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
)
