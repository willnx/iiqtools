# -*- UTF-8 -*-
"""
Unit tests for the iiqtools.utils.shell module
"""
import unittest

from iiqtools.utils import shell
from iiqtools.exceptions import CliError


class TestShell(unittest.TestCase):
    """A suite of test cases for the iiqtools.utils.shell module"""

    def test_happy_path(self):
        """Running a valid command returns an instance of shell.CliResult"""
        result = shell.run_cmd('ls')
        self.assertTrue(isinstance(result, tuple))

    def test_cli_error(self):
        """Running a command that has a non-zero exit code raises CliError"""
        self.assertRaises(CliError, shell.run_cmd, 'not a command')

    def test_cli_result_attributes(self):
        """Verify that the CliResult object attributes remain stable"""
        # NEVER REMOVE OR MODIFY A VALUE IN THIS LIST
        expected = ['command', 'exit_code', 'stderr', 'stdout']
        result = shell.run_cmd('ls')
        for attr in expected:
            self.assertTrue(hasattr(result, attr))


if __name__ == '__main__':
    unittest.main()
