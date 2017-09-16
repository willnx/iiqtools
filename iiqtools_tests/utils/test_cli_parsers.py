# -*- coding: UTF-8 -*-
"""
Unit tests for the iiqtools.utils.cli_parsers module
"""
import os
import json
import unittest

from iiqtools.utils import cli_parsers


def find_examples_dir():
    """Helper function so we can find the example output files regardless from
    where this script runs
    """
    current_location = os.path.abspath(__file__)
    parent_dir = os.path.dirname(current_location)
    return os.path.join(parent_dir, 'cli_parser_examples')

EXAMPLES_DIR = find_examples_dir()


# Individual test cases makes it easy to test just one parser
class TestIfconfigToDict(unittest.TestCase):
    """A suite of test cases for the iiqtools.utils.cli_parsers.ifconfig_to_dict function"""

    def test_ifconfig_to_dict_1(self):
        """Example 1 of `ifconfig` cli output parses to expected structure"""
        with open(os.path.join(EXAMPLES_DIR, 'ifconfig1.json')) as the_file:
            data = json.load(the_file)
        example_output = data['stdout']
        parsed = cli_parsers.ifconfig_to_dict(example_output)

        result = cmp(parsed['interfaces'], data['interfaces'])
        expected = 0 # cmp return zero when values are identical
        self.assertEqual(result, expected)


class TestDfToDict(unittest.TestCase):
    """A suite of test cases for the iiqtools.utils.cli_parsers.df_to_dict function"""

    def test_df_to_dict_1(self):
        """Example 1 of `df` cli output parses to expected structure"""
        with open(os.path.join(EXAMPLES_DIR, 'df1.json')) as the_file:
            data = json.load(the_file)
        example_output = data['stdout']
        parsed = cli_parsers.df_to_dict(example_output)

        result = cmp(parsed['filesystems'], data['filesystems'])
        expected = 0 # cmp return zero when values are identical
        self.assertEqual(result, expected)


class TestMemoryToDict(unittest.TestCase):
    """A suite of test cases for the iiqtools.utils.cli_parsers.memory_to_dict function"""

    def test_memory_to_dict_1(self):
        """Example 1 of `free` cli output parses to expected structure"""
        with open(os.path.join(EXAMPLES_DIR, 'memory1.json')) as the_file:
            data = json.load(the_file)
        example_output = data['stdout']
        parsed = cli_parsers.memory_to_dict(example_output)

        result = cmp(parsed['memory'], data['memory'])
        expected = 0 # cmp return zero when values are identical
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
