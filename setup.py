#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys

from setuptools import setup, find_packages

requires = ['Jinja2>=2.7', 'werkzeug>=0.9', 'itsdangerous', 'misaka', 'html5lib']

if (3, 0) <= sys.version_info < (3, 3):
    raise SystemExit("Python 3.0, 3.1 and 3.2 are not supported")

if sys.version_info < (3, 0):
    requires += ['ipaddress', 'configparser']

setup(
    name='isso',
    version='0.3.dev0',
    author='Martin Zimmermann',
    author_email='info@posativ.org',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    url='https://github.com/posativ/isso/',
    license='BSD revised',
    description='lightweight Disqus alternative',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3"
    ],
    install_requires=requires,
    entry_points={
        'console_scripts':
            ['isso = isso:main'],
    },
)
