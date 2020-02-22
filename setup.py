#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys

from setuptools import setup, find_packages

requires = ['itsdangerous', 'Jinja2', 'misaka', 'html5lib',
            'werkzeug>=1.0', 'bleach', 'flask-caching']

if sys.version_info < (2, 7):
    raise SystemExit("Python 2 versions < 2.7 are not supported.")
elif (3, 0) <= sys.version_info < (3, 4):
    raise SystemExit("Python 3 versions < 3.4 are not supported.")

setup(
    name='isso',
    version='0.12.3',
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
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"
        "Programming Language :: Python :: 3.7"
        "Programming Language :: Python :: 3.8"
    ],
    install_requires=requires,
    extras_require={
        ':python_version=="2.7"': ['ipaddr>=2.1', 'configparser']
    },
    setup_requires=["cffi>=1.3.0"],
    entry_points={
        'console_scripts':
            ['isso = isso:main'],
    }
)
