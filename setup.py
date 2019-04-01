#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = "0.4.2"

setup(
    name='zerophone_hw',
    py_modules=['zerophone_hw'],
    version=version,
    description='ZeroPhone low-level API library. Not to be used by users directly! Is only intended for low-level framework developers and as a hardware reference.',
    author='CRImier',
    author_email='crimier@yandex.ru',
    install_requires=[
        "gpio"
    ],
    entry_points={"console_scripts": ["zerophone_hw = zerophone_hw:main"]},
    url='https://github.com/ZeroPhone/Zerophone-LowLevel-API-Python',
    download_url='https://github.com/ZeroPhone/zerophone-lowlevel-api-python/archive/{}.tar.gz'.format(version),
)
