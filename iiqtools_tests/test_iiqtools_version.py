# -*- coding: UTF-8 -*-
"""
A suite of tests for the iiqtools_version module
"""
import __builtin__
import unittest
from mock import patch

from iiqtools import iiqtools_version


class TestParseCli(unittest.TestCase):
    """A suite of tests for the parse_cli function in iiqtools.iiqtools_version"""

    def test_basic(self):
        """Supplying no args returns an argparse.Namespace object"""
        args = iiqtools_version.parse_cli([])
        self.assertTrue(isinstance(args, iiqtools_version.argparse.Namespace))

    # Mocking away stderr to avoid spam in output while running tests
    @patch.object(iiqtools_version.argparse._sys, 'stderr')
    def test_takes_no_args(self, fake_stderr):
        """iiqtools_version doesn't accept any CLI args (besides -h/--help)"""
        self.assertRaises(SystemExit, iiqtools_version.parse_cli, ['-f'])


class TestMain(unittest.TestCase):
    """A suite of tests for the ``main`` function of iiqtools.iiqtools_version"""

    @patch.object(__builtin__, 'print')
    def test_foo(self, fake_print):
        """InsightIQ and IIQTools are printed to the console"""
        iiqtools_version.main([])
        calls = fake_print.call_args_list

        self.assertEqual(len(calls), 2)

if __name__ == '__main__':
    unittest.main()
