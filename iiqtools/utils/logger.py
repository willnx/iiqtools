# -*- coding: UTF-8 -*-
import logging
import os.path


def get_logger(log_path=None, stream_lvl=0, file_lvl=logging.INFO):
    """Factory for making logging objects

    The verbosity of the logs are configurable as defined by the official Python
    documentation: https://docs.python.org/2/library/logging.html#logging-levels

    :Returns: logging.Logger

    :Raises: AssertionError on bad parameter input

    :param log_path: **Required** The absolute file path to write logs to
    :type log_path: String

    :param stream_lvl: Set to print log messages to the terminal.
    :type stream_lvl: Integer, default 0

    :param file_lvl: How verbose the log file messages are. This value cannot be zero.
    :type stream_lvl: Integer, default 20
    """
    # pylint: disable=line-too-long
    assert stream_lvl in (logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL)
    # pylint: disable=line-too-long
    assert file_lvl in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL)
    assert isinstance(log_path, str) or isinstance(log_path, unicode)
    assert os.path.isabs(log_path)
    assert os.path.isdir(os.path.dirname(log_path))

    # Determine the most verbose log level so both file and stream messages
    # can be accepted by the logging object.
    # Cannot simply take min() of the params because a value of zero means "don't log"
    if stream_lvl:
        base_lvl = min(stream_lvl, file_lvl)
    else:
        base_lvl = file_lvl

    log = logging.getLogger(name=log_path)
    if log.handlers:
        # Calling for the same log multiple times would set multiple handlers
        # If you have 2 duplicate file handers, you write twice to the log file
        return log
    log.setLevel(base_lvl)
    formatter  = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(file_lvl)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(stream_lvl)

    log.addHandler(file_handler)
    log.addHandler(stream_handler)
    return log
