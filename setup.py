#!/usr/bin/env python

from setuptools import find_packages, setup

from shoper import __version__

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='shoper',
    version=__version__,
    author='Daichi Narushima',
    author_email='dnarsil+github@gmail.com',
    description='Simple shell operator module',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dceoy/shoper',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Shells'
    ],
    python_requires='>=3.5'
)
