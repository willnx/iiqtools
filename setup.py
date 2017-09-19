#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from setuptools import setup, find_packages

with open('LICENSE.txt') as the_file:
    license_info = the_file.read()

setup(name="iiqtools",
      author="Nicholas Willhite,",
      author_email="willhite.nicholas@gmail.com",
      url='https://github.com/willnx/iiqtools',
      version='0.2.1',
      packages=find_packages(),
      include_package_data=True,
      scripts=['scripts/iiq_gather_info', 'scripts/iiq_tar_to_zip', 'scripts/iiq_version'],
      license=license_info,
      description="Scripts to help debug and support InsightIQ",
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Systems Administration',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
      ]
     )
