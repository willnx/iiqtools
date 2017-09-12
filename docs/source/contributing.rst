************
Contributing
************

We love contributions from anyone! What's a contribution you ask, well just about
anything.

Feature Requests
================

Got an idea for a script or tool to add to IIQTools, but need some help making it?
File an `issue on Github <https://github.com/willnx/iiqtools/issues>`_.
Please keep in mind that we can't alter InsightIQ source code, so there's literal
zero chance of adding something to the InsightIQ UI.


Bugs
====

What is a bug? Well, anything that impacts your ability to use IIQTools.
This includes things like:

- "the script generated this traceback"
- "your docs are wrong"
- "that script didn't do what I thought it would"

but it's not limited to that. This package exist to make your life easier, so
if part of it is confusing, even some part of the process, let us know by filing
an `issue on Github <https://github.com/willnx/iiqtools/issues>`_.

.. note::

  If it's some sort of code bug, please provide the version of InsightIQ, IIQTools,
  and any tracebacks that were generated. We need that information to fix the bug.


Source code
===========

Wow! Thanks for wanting to add some source code to IIQTools. The process is
pretty standard Github stuff:

1. Fork the repo
#. Add code to your fork
#. Put up a Pull Request to our master branch


There are a few of rules to keep in mind:

A. Write some unit tests. We're not demanding 100% coverage, but the closer the better.
B. Don't incorporate any additional 3rd party libraries. Some of our users cannot
   access the internet, and adding 3rd party libs complicates the install process.
C. Follow our docstring format (look at existing code), and update the docs directory as
   necessary.
