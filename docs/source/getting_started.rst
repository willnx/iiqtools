***************
Getting Started
***************

Install and Upgrade
===================

This section provides directions to install or upgrade the IIQTools package
for your instance of InsightIQ.

.. note::

  The ``--upgrade`` flag is automatically ignored if you're performing an inital install

With Internet connection
------------------------

To install or upgrade the IIQTools package to your instance of InsightIQ run::

  $ sudo su
  $ easy_install --upgrade iiqtools

Without Internet connection
---------------------------

1. Download the package from PyPI
#. Copy the package to the InsightIQ instace
#. Run these commands, replacing ``<package>`` with the actual package name::

   $ sudo su
   $ easy_install --upgrade <package>
