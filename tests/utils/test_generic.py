# -*- UTF-8 -*-
"""
Unit tests for the iiqtools.utils.generic module
"""
import os
import argparse
import unittest
from mock import patch

from iiqtools.utils import generic


class TestGenericUtils(unittest.TestCase):
    """A suite of test cases for the iiqtools.utils.generic module"""

    @patch.object(generic, 'stderr')
    def test_printerr_happy_path(self, mocked_stderr):
        """printerr writes to stderr"""
        generic.printerr('some error')
        self.assertEqual(mocked_stderr.write.call_count, 1)
        self.assertEqual(mocked_stderr.flush.call_count, 1)

    @patch.object(generic, 'stderr')
    def test_printerr_newline(self, mocked_stderr):
        """printerr appends a newline character automatically"""
        generic.printerr('some error')
        args, _ = mocked_stderr.write.call_args
        message = args[0]
        self.assertTrue(message.endswith('\n'))


class TestCheckPath(unittest.TestCase):
    """A suite of tests for the iiqtools.generic.check_path function"""

    def setUp(self):
        """Runs before every test case"""
        self.junk_file = '/tmp/asdfoowersdfuixlwles'

    def tearDown(self):
        """Runs after every test case"""
        try:
            os.remove(self.junk_file)
        except OSError as doh:
            if doh.errno == 2:
                # No such File, ignore
                pass
            else:
                raise

    def test_invalid_path(self):
        """Supplying an invalid file system path raises argparse.ArgumentTypeError"""
        self.assertRaises(argparse.ArgumentTypeError, generic.check_path, 'foo')

    def test_supply_directory(self):
        """Supplying an actual directory returns that value"""
        supplied_value = '/tmp'
        returned_value = generic.check_path(supplied_value)

        self.assertEqual(supplied_value, returned_value)

    def test_supply_file(self):
        """Supplying a file (not a directory) raises argparse.ArgumentTypeError"""
        f = open(self.junk_file, 'w')
        f.close()
        self.assertRaises(argparse.ArgumentTypeError, generic.check_path, self.junk_file)

if __name__ == '__main__':
    unittest.main()
