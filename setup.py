#! /usr/bin/env python

"""Perform setup of the package for build."""
import re
import io

from setuptools import setup


with io.open('eztoml/__init__.py', 'rt', encoding='utf8') as f:
    __version__ = re.search(r'__version__ = "(.*?)"', f.read()).group(1)


test_requires = [
    "pytest~=3.8.2",
    "flake8==2.5.1",
    "pep257==0.7.0",
    "flake8-pep257==1.0.5",
]


setup(
    name='eztoml',
    version=__version__,
    description='Easy TOML',
    install_requires=install_requires,
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
    tests_require=test_requires,
    extras_require={
        'test': test_requires,
    },
    packages=['eztoml'],
)