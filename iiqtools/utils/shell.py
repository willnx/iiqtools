# -*- coding: UTF-8 -*-
"""This module reduces boilerplate when interacting with the command shell, i.e. BASH.

Example A::

    >>> result = shell.run_cmd('ls')
    >>> print result.stdout
    README.txt
    someOtherFile.txt
    >>> print result.stderr

    >>> result.exit_code
    0

Example B::

    >>> # run_cmd does not support the Unix Pipeline
    >>> result = shell.run_cmd('cat foo.txt | grep "not supported"')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
        raise CliError(cli_syntax, stdout, stderr, exit_code)
    iiqtools.exceptions.CliError: Command Failure: cat foo.txt | grep "not supported"
"""
import subprocess
from collections import namedtuple

from iiqtools.exceptions import CliError

_CliResult = namedtuple('CliResult', 'command stdout stderr exit_code')
# Enables us to create a handy docstring for Sphinx
class CliResult(_CliResult):
    """The outcome from running a CLI command

    :Type: collections.namedtuple

    :param command: The CLI command that was ran
    :type command: String

    :param stdout: The output from the standard out stream
    :type stdout: String

    :param stderr: The output from the standard error stream
    :type stderr: String

    :param exit_code: The exit/return code from the command
    :type exit_codee: Integer
    """
    pass

def run_cmd(cli_syntax):
    """Execute a simple CLI command.

    This function blocks until the CLI command returns and does not support the
    Unix pipeline.

    :Returns: CliResult - namedtuple

    :Raises: CliError (when exit code is not zero)

    :param cli_syntax: The CLI command to run.
    :type cli_syntax: String
    """
    CliResult = namedtuple('CliResult', 'command stdout stderr exit_code')
    try:
        proc = subprocess.Popen(cli_syntax.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as doh:
        stdout = ''
        stderr = '%s' % doh
        exit_code = 1
    else:
        stdout, stderr = proc.communicate()
        exit_code = proc.returncode
    if exit_code:
        raise CliError(cli_syntax, stdout, stderr, exit_code)
    else:
        return CliResult(cli_syntax, stdout, stderr, exit_code)
