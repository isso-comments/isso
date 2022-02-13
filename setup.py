#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
import setuptools.command.build_py
import subprocess

from setuptools import setup, find_packages

requires = ['itsdangerous', 'Jinja2', 'misaka>=2.0,<3.0', 'html5lib',
            'werkzeug>=1.0', 'bleach', 'Flask-Caching>=1.9', 'Flask']
tests_require = ['pytest', 'pytest-cov']


class NpmBuildCommand(setuptools.command.build_py.build_py):
    """Prefix Python build with node-based asset build"""

    def run(self):
        # https://tox.wiki/en/latest/config.html#injected-environment-variables
        if 'TOX_ENV_NAME' not in os.environ:
            subprocess.check_call(['make', 'init', 'js'])
        setuptools.command.build_py.build_py.run(self)


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
    python_requires='>=3.5',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9"
    ],
    install_requires=requires,
    tests_require=tests_require,
    entry_points={
        'console_scripts':
            ['isso = isso:main'],
    },
    cmdclass={
        'build_py': NpmBuildCommand,
    },
)
