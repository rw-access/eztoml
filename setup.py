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
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    packages=['eztoml'],
    tests_require=["PyYAML~=5.3"],
    entry_points={
        'console_scripts': [
            'toml-lint=eztoml:lint_files',
        ],
        'pygments.lexers': [
            'eql=eql.highlighters:EqlLexer'
        ]
    },
)
