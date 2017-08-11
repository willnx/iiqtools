# -*- coding: UTF-8 -*-
"""
Unit tests for the iiqtools.utils.logger module
"""
import logging
import unittest

from iiqtools.utils.logger import get_logger


class TestGetLogger(unittest.TestCase):
    """A suite of test cases for the iiqtools.utils.logger module"""

    def setUp(self):
        """Runs before every test case"""
        # clear out all logger objects
        logging.Logger.manager.loggerDict = {}

    def test_happy_path(self):
        """You'll get a logger if you only supply a valid path to log to"""
        log = get_logger(log_path='/dev/null')
        self.assertTrue(isinstance(log, logging.Logger))

    def test_bad_path(self):
        """AssertionError is raised for an invalid file system path"""
        self.assertRaises(AssertionError, get_logger, log_path='not a path')

    def test_bad_stream_lvl(self):
        """AssertionError is raised if the param stream_lvl is not a valid integer"""
        self.assertRaises(AssertionError, get_logger, log_path='/dev/null', stream_lvl=9001)

    def test_bad_file_lvl(self):
        """AssertionError is raised if the param file_lvl is not a valid integer"""
        self.assertRaises(AssertionError, get_logger, log_path='/dev/null', file_lvl=9001)

    def test_log_level_no_stream(self):
        """The log level will be the value of file_lvl when stream_lvl is zero"""
        file_lvl = 30
        log = get_logger(log_path='/dev/null', file_lvl=file_lvl)
        self.assertEqual(log.level, file_lvl)

    def test_log_level_with_stream(self):
        """The log level will be the lower value between stream_lvl and file_lvl"""
        stream_lvl = 20
        file_lvl = 40
        log =  get_logger(log_path='/dev/null', file_lvl=file_lvl, stream_lvl=stream_lvl)
        self.assertEqual(log.level, stream_lvl)

    def test_calling_get_logger_mutiple_times(self):
        """Asking for the same logger multiple times returns the same object"""
        log1 = get_logger(log_path='/dev/null')
        log2 = get_logger(log_path='/dev/null')
        self.assertTrue(log1 is log2)

    def test_get_logger_mutiple_times_no_extra_handlers(self):
        """Asking for the same logger multiple times returns the same object
        without adding more handelers
        """
        log1 = get_logger(log_path='/dev/null')
        log1_handler_count = len(log1.handlers)
        log2 = get_logger(log_path='/dev/null')
        log2_handler_count = len(log2.handlers)
        self.assertTrue(log1_handler_count is log2_handler_count)


if __name__ == '__main__':
    unittest.main()
