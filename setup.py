#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import re

from setuptools import setup, find_packages

version = re.search("__version__ = '([^']+)'",
                    open('isso/__init__.py').read()).group(1)

setup(
    name='isso',
    version=version,
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
        "Programming Language :: Python :: 2.7"
    ],
    install_requires=['mako', 'itsdangerous'],
    entry_points={
        'console_scripts':
            ['isso = isso:main'],
    },
)
