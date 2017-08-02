#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='zerophone_hw',
    py_modules=['zerophone_hw'],
    version="0.1.0",
    description='ZeroPhone API library',
    author='CRImier',
    author_email='crimier@yandex.ru',
    install_requires=[
        "gpio"
    ],
    url = 'https://github.com/ZeroPhone/zerophone-api-py',
    download_url = 'https://github.com/ZeroPhone/zerophone-api-py/archive/0.1.0.tar.gz'
)
