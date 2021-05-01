#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys

from setuptools import setup, find_packages

requires = [
    "bleach",
    "flask-caching>=1.9",
    "html5lib",
    "itsdangerous",
    "Jinja2",
    "misaka>=2.0,<3.0",
    "requests>=2.25,<2.26",
    "werkzeug>=1.0",
]

if sys.version_info < (3, ):
    raise SystemExit("Python 2 is not supported.")
elif (3, 0) <= sys.version_info < (3, 5):
    raise SystemExit("Python 3 versions < 3.5 are not supported.")

setup(
    name='isso',
    version='0.12.5',
    author='Martin Zimmermann',
    author_email='info@posativ.org',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    url='https://github.com/posativ/isso/',
    license='MIT',
    description='lightweight Disqus alternative',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8"
    ],
    install_requires=requires,
    setup_requires=["cffi>=1.3.0"],
    entry_points={
        'console_scripts':
            ['isso = isso:main'],
    }
)
