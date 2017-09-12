# -*- coding: UTF-8 -*-
"""
Utilities for interacting with the InsightIQ database
"""
from collections import namedtuple

import psycopg2

from iiqtools.exceptions import DatabaseError


_Column = namedtuple('Column', 'name type')

# This allows us to define the docstring for out namedtuple
class Column(_Column):
    """A database column consiting of the column's name, and it's type

    :Type: namedtuple

    :param name: The column's name

    :param type: The database type for the given column (i.e. int, float, double)
    """
    pass

# This database abstraction intentionally does not comply with PEP 249
# https://www.python.org/dev/peps/pep-0249/
# Why? It's a bit much if you're not an experienced developer or you only
# need to perform simple interactions with a database. The point of this
# abstraction to have a simple, easy to use object for poking the IIQ database
class Database(object):
    """Simplifies communication with the database.

    The goal of this object is to make basic interactions with the database
    simpler than directly using the psycopg2 library. It does this by reducing
    the number of API methods, providing handy built-in methods for common needs
    (like listing tables of a database), auto-commit of transactions, and
    auto-rollback of bad SQL transactions.
    This object is not indented for power users, or long lived processes (like
    the InsightIQ application); it's designed for shorter lived "scripts".

    :param user: The username when connection to the databse
    :type user: String, default postgres

    :param dbname: The specific database to connection to. InsightIQ utilizes
                   a different database for every monitored cluster, plus one
                   generic database for the application (named "insightiq").
    :type dbname: String, default insightiq
    """
    def __init__(self, user='postgres', dbname='insightiq'):
        self._connection = psycopg2.connect(user=user, dbname=dbname)
        self._cursor = self._connection.cursor()
        if dbname == 'insightiq':
            self.execute("SET search_path to admin,iiq,public;")

    def __enter__(self):
        """Enables use of the ``with`` statement to auto close database connection
        https://docs.python.org/2.7/reference/datamodel.html#with-statement-context-managers

        Example::

          with Database() as db:
              print db.cluster_databases
        """
        return self

    def __exit__(self, exc_type, exc_value, the_traceback):
        self._connection.close()

    def execute(self, sql, params=None):
        """Run a single SQL command

        :Returns: Generator

        :param sql: **Required** The SQL syntax to execute
        :type sql: String

        :param params: The values to use in a parameterized SQL query
        :type params: Iterable

        This method is implemented as a Python Generator:
        https://wiki.python.org/moin/Generators
        This means you are suppose to iterate over the results::

            db = Database()
            for row in db.execute("select * from some_table;"):
                print row

        If you want all the rows as a single thing, just use ``list``::

            db = Database()
            data = list(db.execute("select * from some_table;")

        But **WARNING** that might cause your program to run out of memory and crash!
        That reason is why this method is a generator by default ;)

        To perform a parameterized query (i.e. avoid SQL injection), provided
        the parameters as an iterable::

            db = Database()
            # passing in "foo_column" alone would try and string format every
            # character of "foo_column" into your SQL statement.
            # Instead, make "foo_column" a tuple by wrapping it like ("foo_column",)
            # Note: the trailing comma is required.
            data = list(db.execute("select %s from some_table", ("foo_column",)))
        """
        return self._query(sql, params=params, many=False)

    def executemany(self, sql, params):
        """Run the SQL for every iteration of the supplied params

        This method behaves exactly like `execute`, except that it can perform
        multiple SQL commands in a single transaction. The point of this method
        is so you can retain Atomicity when you must execute the same SQL with
        different parameters. This method isn't intended to be faster than
        looping over the normal `execute` method with the different parameters.

        :Returns: Generator

        :param sql: **Required** The SQL syntax to execute
        :type sql: String

        :param params: **Required** The parameterized values to iterate
        :type params: Iterable
        """
        return self._query(sql, params=params, many=True)

    def _query(self, sql, params=None, many=False):
        """Internal method for running SQL commands

        The code difference between execute, and executemany is just the method
        we call on the cursor object.

        :Returns: Generator

        :param sql: **Required** The SQL syntax to execute
        :type sql: String

        :param params: The values to use in a parameterized SQL query
        :type params: Iterable

        :param many: Set to True to call `executemany`
        :type many: Boolean, default is False
        """
        if many:
            call = getattr(self._cursor, 'executemany')
        else:
            call = getattr(self._cursor, 'execute')
        try:
            call(sql, params)
            self._connection.commit()
        except psycopg2.Error as doh:
            # All psycopg2 Exceptions are subclassed from psycopg2.Error
            self._connection.rollback()
            raise DatabaseError(message=doh.pgerror, pgcode=doh.pgcode)
        else:
            data = self._cursor.fetchone()
            while data:
                yield data
                data = self._cursor.fetchone()

    @property
    def isolation_level(self):
        """Set the isolation level of your connnection to the database"""
        # To drop tables, you'll have to set isolation_level to 0 (zero)
        # https://www.postgresql.org/docs/current/static/transaction-iso.html
        return self._connection.isolation_level

    @isolation_level.setter
    def isolation_level(self, value):
        # https://www.postgresql.org/docs/current/static/transaction-iso.html
        self._connection.set_isolation_level(value)

    def tables(self):
        """Obtain a list of all the tables for the database you're connected to

        :Returns: List
        """
        sql = """SELECT relname FROM pg_class WHERE relkind='r' AND relname !~ '^(pg_|sql_)';"""
        # data looks like [('sometable1',), ('sometable2',)]
        # drop all the tuples, so we just return a list of strings
        return [x[0] for x in self.execute(sql)]

    def cluster_databases(self):
        """Obtain a list of all the cluster databases

        :Returns: List
        """
        sql = """SELECT datname from pg_database;"""
        dbs = list(self.execute(sql))
        ignore = ('template0', 'template1', 'postgres', 'insightiq')
        return [x[0] for x in dbs if x[0] not in ignore]

    def table_schema(self, table):
        """Given a table, return the schema for that table

        :Returns: Tuple of namedtuples -> (Column(name, type), Column(name, type))

        :param table: **Required** The table to obtain the primary key from
        :type table: String
        """
        sql = """SELECT column_name, data_type
                 FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s;"""
        return tuple([Column(x[0], x[1]) for x in self.execute(sql, (table,))])

    def primary_key(self, table):
        """Given a table, return the primary key

        .. note::

            If you supply a timeseries table that DOES NOT have an EPOC timestamp
            in the name, you will get zero results. For timeseries tables,
            supply a table that contains the EPOC timestamps to see the primary key.

        :Returns: Tuple of namedtuples -> (Column(name, type), Column(name, type))

        :param table: **Required** The table to obtain the primary key from
        :type table: String
        """
        sql = """SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS data_type
                 FROM   pg_index i
                 JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                        AND a.attnum = ANY(i.indkey)
                 WHERE  i.indrelid = %s::regclass
                 AND    i.indisprimary;"""
        return tuple([Column(x[0], x[1]) for x in self.execute(sql, (table,))])

    def close(self):
        """Disconnect from the database"""
        self._connection.close()
