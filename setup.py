#!/usr/bin/env python

from setuptools import setup, find_packages
from shopy import __version__


setup(
    name='shopy',
    version=__version__,
    description='Pandas-based Data Handlers for DNA-sequencing',
    packages=find_packages(),
    author='Daichi Narushima',
    author_email='dnarsil+github@gmail.com',
    url='https://github.com/dceoy/shopy',
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ],
    long_description="""\
shopy
-----

Simple shell operator module for Python
"""
)
