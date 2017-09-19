.. image:: https://travis-ci.org/willnx/iiqtools.svg?branch=master
    :target: https://travis-ci.org/willnx/iiqtools

.. image:: https://readthedocs.org/projects/iiqtools/badge/
    :target: http://iiqtools.readthedocs.io/en/latest/?badge=latest

########
IIQTools
########

This package contains scripts to help debug and support InsightIQ.

InsightIQ is a web-app developed by Dell EMC for your Isilon OneFS cluster.
It runs "off-cluster" and collects statistics about the file system and other various
performance metrics. Users of InsightIQ rely on that data to:

- Optimize storage resources
- Forecast future needs
- Identify performance bottlenecks
- Export Isilon specific data to "in house" analytic tools


********************
Installing/Upgrading
********************

If you have access to `PyPi <https://pypi.python.org/pypi/iiqtools>`_ and
`Python pip <https://pip.pypa.io/en/stable/installing/>`_ is already installed, you
should be able to simply run this command on your InsightIQ instance::

  sudo pip install -U iiqtools

For full documentation, checkout:

http://iiqtools.readthedocs.io/en/latest/getting_started.html#install-and-upgrade

*************
Documentation
*************

The documentation is auto-generated upon merge to the master branch, and can
be found at:

http://iiqtools.readthedocs.io/en/latest/index.html

************
Contributing
************

Found a bug? Got a feature request? Want to add your own script?
We love getting feedback from the community. For details checkout:

http://iiqtools.readthedocs.io/en/latest/contributing.html
