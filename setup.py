#!/usr/bin/env python
# -*- coding: utf-8
from sys import version_info
from setuptools import setup

setup(
    name='aixplot',
    version='0.1.0',
    description='Simple "live plotter" for Jupyter',
    author='Lukas Koschmieder',
    author_email='lukas.koschmieder@rwth-aachen.de',
    license='MIT',
    url='https://github.com/lukas-koschmieder/aixplot',
    requires=['bqplot', 'ipywidgets'],
    packages=['aixplot'],
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Software Development'],
    keywords=['Plot', 'Visualization', 'Jupyter', 'JupyterLab', 'Widget'],
)
