#! /usr/bin/env python

"""Perform setup of the package for build."""
import re
import io

from setuptools import setup


with io.open('eztoml/__init__.py', 'rt', encoding='utf8') as f:
    __version__ = re.search(r'__version__ = "(.*?)"', f.read()).group(1)


setup(
    name='eztoml',
    version=__version__,
    description='Easy TOML',
    author='Ross Wolf',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Database',
        'Topic :: Internet :: Log Analysis',
        'Topic :: Scientific/Engineering :: Information Analysis',
    ],
    url='https://eztoml.readthedocs.io',
    packages=['eztoml'],
)
