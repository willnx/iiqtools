#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from setuptools import setup, find_packages

with open('LICENSE.txt') as the_file:
    license_info = the_file.read()

setup(name="iiqtools",
      author="Nicholas Willhite,",
      author_email="willhite.nicholas@gmail.com",
      url='https://github.com/willnx/iiqtools',
      version='2.0.0',
      packages=find_packages(),
      include_package_data=True,
      scripts=['scripts/iiqtools_gather_info',
               'scripts/iiqtools_tar_to_zip',
               'scripts/iiqtools_version',
               'scripts/iiqtools_patch'],
      license=license_info,
      description="Scripts to help debug and support InsightIQ",
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Systems Administration',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
      ]
     )
