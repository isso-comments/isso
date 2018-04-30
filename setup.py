#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys

from setuptools import setup, find_packages

<<<<<<< HEAD
requires = ['html5lib==0.9999999', 'itsdangerous', 'Jinja2',
            'misaka>=1.0,<2.0', 'werkzeug>=0.9', 'uwsgi']
=======
requires = ['itsdangerous', 'Jinja2', 'misaka>=2.0,<3.0', 'html5lib<0.9999999',
            'werkzeug>=0.9']
>>>>>>> e745f326db2ec1c39a4aae9094ef4891c9687e4a

if sys.version_info < (2, 7):
    raise SystemExit("Python 2 versions < 2.7 are not supported.")
elif (3, 0) <= sys.version_info < (3, 4):
    raise SystemExit("Python 3 versions < 3.4 are not supported.")

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
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"
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
