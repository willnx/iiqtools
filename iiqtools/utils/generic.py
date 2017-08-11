# -*- coding: UTF-8 -*-
"""
This module contains miscellaneous utility functions
"""
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
