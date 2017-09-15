# -*- coding: UTF-8 -*-
"""
This module contains miscellaneous utility functions
"""
import os.path
import argparse
from sys import stderr


def printerr(message):
    """Just like print(), but outputs to stderr.

    :Returns: None

    :param message: The thing to write to stderr
    :type message: PyObject
    """
    msg = '%s\n' % message # print() auto-inserts a line return too
    stderr.write(msg)
    stderr.flush()


def check_path(cli_value):
    """Validate that the supplied path is an actual file system directory.

    This function is intended to be used with the argparse lib as an
    `argument type <https://docs.python.org/2.7/library/argparse.html#type>`_.

    :Raises: argparse.ArgumentTypeError

    :Returns: String

    :param cli_value: The value supplied by the end user
    :type cli_value: String
    """
    if not os.path.isdir(cli_value):
        msg = 'Supplied value is not a directory, %s' % (cli_value)
        raise argparse.ArgumentTypeError(msg)
    else:
        return cli_value
