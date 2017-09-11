***************
Getting Started
***************

Install and Upgrade
===================

This section provides directions to install or upgrade the IIQTools package
for your instance of InsightIQ.

.. note::

  The ``--upgrade`` flag is automatically ignored if you're performing an initial install

With Internet connection
------------------------

To install or upgrade the IIQTools package to your instance of InsightIQ run::

  $ sudo su
  $ easy_install --upgrade iiqtools

Without Internet connection
---------------------------

1. Download the package from `PyPI <https://pypi.python.org/pypi/iiqtools>`_
#. Copy the package to the InsightIQ instance
#. Run these commands, replacing ``<package>`` with the actual package name::

   $ sudo su
   $ easy_install --upgrade <package>


Setting up a development environment
====================================

This section is *only* for settings up a development environment. Only follow
these directions if you intend to contribute source code to the project.

If you have the *know-how* to build and test IIQTools on MacOS or Windows, we'd
love to get a `Pull Request <https://github.com/willnx/iiqtools>`_ from you updating this section!


Linux
-----

These are non-Python libraries required to build and test IIQTools.
Use the builtin packagemanger (i.e. apt-get, yum, dnf) to install these packages.

RHEL/CentOS/Fedora:

- make
- python-devel
- postgresql-devel
- postgresql
- redhat-rpm-config


Before installing the Python dependencies, it's highly encouraged to configure a
`Python Virtualenv <https://virtualenv.pypa.io/en/stable/>`_ for working with IIQTools.


Once you've got your virtualenv configured and activated, run this command to
install the dependencies for building and testing IIQTools::

  $ pip install -r requirements-dev.txt

Once you've installed those dependencies, you can run all the unit tests like this::

  $ make test

And generate the docs with::

  $ make docs

Or clean up everything with::

  $ make clean
