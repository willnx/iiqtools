# -*- coding: UTF-8 -*-
"""
A suite of tests for the iiq_version module
"""
import __builtin__
import unittest
from mock import patch

from iiqtools import iiq_version


class TestParseCli(unittest.TestCase):
    """A suite of tests for the parse_cli function in iiqtools.iiq_version"""

    def test_basic(self):
        """Supplying no args returns an argparse.Namespace object"""
        args = iiq_version.parse_cli([])
        self.assertTrue(isinstance(args, iiq_version.argparse.Namespace))

    # Mocking away stderr to avoid spam in output while running tests
    @patch.object(iiq_version.argparse._sys, 'stderr')
    def test_takes_no_args(self, fake_stderr):
        """iiq_version doesn't accept any CLI args (besides -h/--help)"""
        self.assertRaises(SystemExit, iiq_version.parse_cli, ['-f'])


class TestMain(unittest.TestCase):
    """A suite of tests for the ``main`` function of iiqtools.iiq_version"""

    @patch.object(__builtin__, 'print')
    def test_foo(self, fake_print):
        """InsightIQ and IIQTools are printed to the console"""
        iiq_version.main([])
        calls = fake_print.call_args_list

        self.assertEqual(len(calls), 2)

if __name__ == '__main__':
    unittest.main()
