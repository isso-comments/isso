#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys

from setuptools import setup, find_packages

requires = ['itsdangerous', 'misaka>=1.0,<2.0', 'html5lib==0.9999999', 'Jinja2']

if (3, 0) <= sys.version_info < (3, 3):
    raise SystemExit("Python 3.0, 3.1 and 3.2 are not supported")

setup(
    name='isso',
    version='0.10.7.dev0',
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
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4"
    ],
    install_requires=requires,
    extras_require={
        ':python_version=="2.6"': ['argparse', 'ordereddict'],
        ':python_version=="2.6" or python_version=="2.7"': ['ipaddr>=2.1', 'configparser', 'werkzeug>=0.8'],
        ':python_version!="2.6" and python_version!="2.7"': ['werkzeug>=0.9']
    },
    entry_points={
        'console_scripts':
            ['isso = isso:main'],
    }
)
