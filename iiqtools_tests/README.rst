############
Unit testing
############

This entire directory structure contains all the unit tests for the iiqtools
package.

It's expected that all code contributions are accompanied by unit tests.
Unfamiliar with unit testing? No worries! We're more than happy to help you out!
The major point of unit tests is to help with maintainability of the software;
it enables us to add features and fix bugs while avoiding regressions or breaking
other functional areas.

The general layout of the tests should mirror the package. For example::

  iiqtools
    exceptions.py
    \utils
      logger.py
      shell.py


  tests
    test_exceptions.py
    \utils
      test_logger.py
      test_shell.py


This just makes it easier for humans to understand "which tests go with which module."
