import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/grading-standard-lti>`_.
"""

version_path = "grading_standard/VERSION"
VERSION = open(os.path.join(os.path.dirname(__file__), version_path)).read()
VERSION = VERSION.replace("\n", "")

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="UW-Grading-Standard-LTI",
    version=VERSION,
    packages=["grading_standard"],
    include_package_data=True,
    install_requires = [
        "django~=5.2",
        "django-blti~=3.0",
        "django-compressor",
        "uw-memcached-clients~=1.0",
        "uw-restclients-core~=1.4",
        "uw-restclients-canvas~=1.2",
    ],
    license="Apache License, Version 2.0",
    description=(
        "An LTI app for creating 4.0 grading standards and adding them to a "
        "Canvas course"),
    long_description=README,
    url="https://github.com/uw-it-aca/grading-standard-lti",
    author="UW-IT Student & Educational Technology Services",
    author_email="aca-it@uw.edu",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
)
