# -*- UTF-8 -*-
"""
Unit tests for the iiqtools.utils.generic module
"""
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


if __name__ == '__main__':
    unittest.main()
