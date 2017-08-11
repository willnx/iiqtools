# -*- UTF-8 -*-
"""
Centralized location for all custom Exceptions
"""

class CliError(Exception):
    """Raised when an CLI command has a non-zero exit code

    :attribute command: The CLI syntax that had a non-zero exit code
    :attribute stdout: The standard output from the command
    :attribute stderr: The standard error from the command
    :attribute exit_code: The exit code of the command
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
