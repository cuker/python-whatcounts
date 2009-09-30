#!/usr/bin/env python

from distutils.core import setup

from whatcounts import __version__ as version

setup(
    name = 'whatcounts',
    version = version,
    description = 'WhatCounts Library',
    author = 'Lefora',
    author_email = 'samuel@lefora.com',
    url = 'http://github.com/samuel/python-whatcounts',
    packages = ['whatcounts'],
    classifiers = [
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
