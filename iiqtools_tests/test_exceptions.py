# -*- coding: UTF-8 -*-
"""
Unit tests for the iiqtools.exceptions module
"""

import unittest

from iiqtools import exceptions


class TestExceptions(unittest.TestCase):
    """A suite of test cases for the iiqtools.exceptions module"""

    def test_cli_error(self):
        """CliError is a valid exception"""
        exception = exceptions.CliError(command='foo', stdout='woot', stderr='boo', exit_code=1)
        self.assertTrue(isinstance(exception, exceptions.CliError))

    def test_database_error(self):
        """DatabaseError is a valid exception"""
        exception = exceptions.DatabaseError(message='oops', pgcode='asdf')
        self.assertTrue(isinstance(exception, exceptions.DatabaseError))


if __name__ == '__main__':
    unittest.main()
