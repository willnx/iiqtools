# -*- UTF-8 -*-
"""
Centralized location for all custom Exceptions
"""

class CliError(Exception):
    """Raised when an CLI command has a non-zero exit code.

    :param command: The CLI command that was ran
    :type command: String

    :param stdout: The output from the standard out stream
    :type stdout: String

    :param stderr: The output from the standard error stream
    :type stderr: String

    :param exit_code: The exit/return code from the command
    :type exit_codee: Integer
    """
    def __init__(self, command, stdout, stderr, exit_code, message='Command Failure'):
        msg = '%s: %s' % (message, command)
        super(CliError, self).__init__(msg)
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code


class DatabaseError(Exception):
    """Raised when an error occurs when interacting with the InsightIQ database

    :attribute pgcode: The error code used by PostgreSQL. https://www.postgresql.org/docs/9.3/static/errcodes-appendix.html
    :attribute message: The error message
    """
    def __init__(self, message, pgcode):
        super(DatabaseError, self).__init__(message)
        self.pgcode = pgcode
