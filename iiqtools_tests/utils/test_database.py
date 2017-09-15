# -*- coding: UTF-8 -*-
"""
Unit tests for the iiqtools.utils.database module
"""
import types
import unittest
from mock import MagicMock, patch

import iiqtools.utils.database as database


class TestDatabase(unittest.TestCase):
    """A suite of tests for the iiqtools.utils.database module"""

    def setUp(self):
        """Runs before every test case"""
        # mock away the psycopg2 module
        self.patcher = patch('iiqtools.utils.database.psycopg2')
        self.mocked_psycopg2 = self.patcher.start()
        self.mocked_connection = MagicMock()
        self.mocked_cursor = MagicMock()
        self.mocked_psycopg2.connect.return_value = self.mocked_connection
        self.mocked_connection.cursor.return_value = self.mocked_cursor
        # General mocked response
        self.mocked_cursor.fetchone.side_effect = [('foo', 'string'), ('bar', 'string'), StopIteration('test')]

    def tearDown(self):
        """Runs after every test case"""
        self.patcher.stop()

    def test_init(self):
        """Simple test that we can instantiate Database class for testing"""
        db = database.Database()
        self.assertTrue(isinstance(db, database.Database))
        self.assertTrue(db._connection is self.mocked_connection)
        self.assertTrue(db._cursor is self.mocked_cursor)

    def test_context_manager(self):
        """Database support use of `with` statement and auto-closes connection"""
        with database.Database() as db:
            pass
        self.assertTrue(self.mocked_connection.close.call_count is 1)

    def test_close(self):
        """Calling Database.close() closes the connection to the DB"""
        db = database.Database()
        db.close()
        self.assertTrue(self.mocked_connection.close.call_count is 1)

    def test_isolation_level_getter(self):
        """Property Database.isolation_level returns connection's isolation level"""
        self.mocked_connection.isolation_level = 1
        db = database.Database()
        isolation_level = db.isolation_level

        self.assertTrue(isolation_level is 1)

    def test_isolation_level_setter(self):
        """Property Database.isolation_level can set value"""
        db = database.Database()
        db.isolation_level = 7

        args, _ = self.mocked_connection.set_isolation_level.call_args
        sent_level = args[0]
        expected = 7

        self.assertEqual(sent_level, expected)

    def test_executemany(self):
        """Happy path test for the Database.executemany method"""
        db = database.Database()
        result = db.executemany(sql="SELECT * from FOO WHERE bar = %s", params=('bat',))
        self.assertTrue(isinstance(result, types.GeneratorType))

    def test_primary_key(self):
        """Method `primary_key` returns a tuple of database.Column objects"""
        db = database.Database()
        primary_key = db.primary_key(table='sometable')
        expected = (database.Column('foo', 'string'), database.Column('bar', 'string'))

        self.assertEqual(primary_key, expected)

    def test_table_schema(self):
        """Method `table_schema` returns a tuple of database.Column objects"""
        db = database.Database()
        schema = db.table_schema(table='sometable')
        expected = (database.Column('foo', 'string'), database.Column('bar', 'string'))

        self.assertEqual(schema, expected)

    def test_cluster_databases(self):
        """Method `cluster_databases` returns a list of the databases"""
        db = database.Database()
        cluster_dbs = db.cluster_databases()
        expected = ['foo', 'bar']

        self.assertEqual(cluster_dbs, expected)

    def test_tables(self):
        """Method `tables` returns a list of tables in the databases"""
        db = database.Database()
        tables = db.tables()
        expected = ['foo', 'bar']

        self.assertEqual(tables, expected)


if __name__ == '__main__':
    unittest.main()
