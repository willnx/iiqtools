#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from setuptools import setup, find_packages
from os import environ

with open('LICENSE.txt') as the_file:
    license_info = the_file.read()

setup(name="iiqtools",
      author="Nicholas Willhite,",
      version='0.0.%s' % environ.get('BUILD_NUMBER', '0'),
      packages=find_packages(),
      include_package_data=True,
      scripts=['scripts/iiq_gather_info'],
      license=license_info,
      description="Scripts to help debug and support InsightIQ",
      )
