#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = "0.2.0"

setup(
    name='zerophone_hw',
    py_modules=['zerophone_hw'],
    version=version,
    description='ZeroPhone API library',
    author='CRImier',
    author_email='crimier@yandex.ru',
    install_requires=[
        "gpio"
    ],
    url = 'https://github.com/ZeroPhone/Zerophone-API-Python',
    download_url = 'https://github.com/ZeroPhone/zerophone-api-py/archive/{}.tar.gz'.format(version)
)
