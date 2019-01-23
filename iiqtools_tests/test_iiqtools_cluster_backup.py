# -*- UTF-8 -*-
"""
Unit tests for the iiqtools.iiqtools_cluster_backup tool
"""
import json
import unittest
import argparse
import StringIO

from mock import patch, MagicMock

from iiqtools import iiqtools_cluster_backup
from iiqtools.utils.insightiq_api import Parameters, ConnectionError


class TestClusterBackupCliArgs(unittest.TestCase):
    """A suite of tests for the iiqtools_cluster_backup CLI"""

    def test_parse_args_namespace(self):
        """parse_args returns argparse.Namespace object"""
        cli_args = ['--show-clusters']

        result = iiqtools_cluster_backup.parse_args(cli_args)

        self.assertTrue(isinstance(result, argparse.Namespace))

    @patch.object(iiqtools_cluster_backup.argparse._sys, 'stderr')
    def test_parse_args_mutex(self, fake_stderr):
        """parse_args, --show-clusters and --clusters is mutually exclusive"""
        cli_args = ['--show-clusters', '--clusters', 'myCluster']

        with self.assertRaises(SystemExit):
            iiqtools_cluster_backup.parse_args(cli_args)

    def test_clusters_required(self):
        """parse_args, supplying --clusters requires --location, --username, and --password"""
        cli_args = ['--clusters', 'myCluster', '--location', '/foo', '--username', 'pat', '--password', 'a']

        result = iiqtools_cluster_backup.parse_args(cli_args)

        self.assertTrue(isinstance(result, argparse.Namespace))

    @patch.object(iiqtools_cluster_backup.argparse._sys, 'stderr')
    def test_clusters_location(self, fake_stderr):
        """parse_args rasies SystemExit  if --location isn't supplied with --clusters"""
        cli_args = ['--clusters', 'myCluster', '--username', 'pat', '--password', 'a']

        with self.assertRaises(SystemExit):
            iiqtools_cluster_backup.parse_args(cli_args)

    @patch.object(iiqtools_cluster_backup.argparse._sys, 'stderr')
    def test_clusters_username(self, fake_stderr):
        """parse_args rasies SystemExit  if --username isn't supplied with --clusters"""
        cli_args = ['--clusters', 'myCluster', '--location', '--password', 'a']

        with self.assertRaises(SystemExit):
            iiqtools_cluster_backup.parse_args(cli_args)

    @patch.object(iiqtools_cluster_backup.argparse._sys, 'stderr')
    @patch.object(iiqtools_cluster_backup.getpass, 'getpass')
    def test_password_prompt(self, fake_getpass, fake_stderr):
        """parse_args prompts for password if it's not supplied"""
        cli_args = ['--clusters', 'myCluster', '--location', '/foo', '--username', 'pat']

        iiqtools_cluster_backup.parse_args(cli_args)

        fake_getpass.assert_called()

    def test_many_clusters(self):
        """parse_args accepts a list of clusters as a value for --clusters"""
        cli_args = ['--clusters', 'myCluster', 'myOtherCluster', '--location', '/foo', '--username', 'pat', '--password', 'a']

        result = iiqtools_cluster_backup.parse_args(cli_args)

        expected = ['myCluster', 'myOtherCluster']
        actual = result.clusters

        self.assertEqual(expected, actual)

    def test_all_clusters(self):
        """parse_args support the ``--all-clusters`` argument"""
        cli_args = ['--all-clusters', '--location', '/foo', '--username', 'alice', '--password', 'a']

        result = iiqtools_cluster_backup.parse_args(cli_args)

        expected = True
        actual = result.all_clusters

        self.assertEqual(expected, actual)

    @patch.object(iiqtools_cluster_backup.zipfile, 'is_zipfile')
    @patch.object(iiqtools_cluster_backup.os.path, 'isfile')
    def test_inspect(self, fake_isfile, fake_is_zipfile):
        """parse_args supports the ``--inspect`` argument"""
        fake_isfile.return_value = True
        fake_is_zipfile.return_value = True
        cli_args = ['--inspect', 'insightiq_export_1234567890.zip']

        result = iiqtools_cluster_backup.parse_args(cli_args)

        expected = 'insightiq_export_1234567890.zip'
        actual = result.inspect

        self.assertEqual(expected, actual)

    @patch.object(iiqtools_cluster_backup.zipfile, 'is_zipfile')
    @patch.object(iiqtools_cluster_backup.os.path, 'isfile')
    def test_inspect_is_file(self, fake_isfile, fake_is_zipfile):
        """parse_args - The ``--inspect`` argument raises SystemExit if the value is not a file"""
        fake_isfile.return_value = False
        fake_is_zipfile.return_value = True
        cli_args = ['--inspect', 'insightiq_export_1234567890.zip']

        with self.assertRaises(SystemExit):
            iiqtools_cluster_backup.parse_args(cli_args)

    @patch.object(iiqtools_cluster_backup.zipfile, 'is_zipfile')
    @patch.object(iiqtools_cluster_backup.os.path, 'isfile')
    def test_inspect_is_zipfile(self, fake_isfile, fake_is_zipfile):
        """parse_args - The ``--inspect`` argument raises SystemExit if the value is not a zipfile"""
        fake_isfile.return_value = True
        fake_is_zipfile.return_value = False
        cli_args = ['--inspect', 'insightiq_export_1234567890.zip']

        with self.assertRaises(SystemExit):
            iiqtools_cluster_backup.parse_args(cli_args)

    @patch.object(iiqtools_cluster_backup.zipfile, 'is_zipfile')
    @patch.object(iiqtools_cluster_backup.os.path, 'isfile')
    def test_inspect_bad_name(self, fake_isfile, fake_is_zipfile):
        """parse_args - The ``--inspect`` argument raises SystemExit if the value is not correctly named"""
        fake_isfile.return_value = True
        fake_is_zipfile.return_value = True
        cli_args = ['--inspect', 'insightiq_export_123.zip']

        with self.assertRaises(SystemExit):
            iiqtools_cluster_backup.parse_args(cli_args)


class TestClusterBackupCleanupBackups(unittest.TestCase):
    """A suite of test cases for the _cleanup_backups function"""

    @patch.object(iiqtools_cluster_backup, 'os')
    def test_max_backups_zero(self, fake_os):
        """Returns None and bails earily when param max_backups is zero"""
        result = iiqtools_cluster_backup._cleanup_backups(location='/tmp', max_backups=0)
        expected = None

        listdir_calls = fake_os.listdir.call_count
        expected_calls = 0

        self.assertEqual(result, expected)
        self.assertEqual(listdir_calls, expected_calls)

    @patch.object(iiqtools_cluster_backup.os.path, 'isfile')
    @patch.object(iiqtools_cluster_backup.os, 'remove')
    @patch.object(iiqtools_cluster_backup.os, 'listdir')
    def test_no_backups_found(self, fake_listdir, fake_remove, fake_isfile):
        """Nothing is deleted if there are no backups files found"""
        fake_isfile.return_value = True
        fake_listdir.return_value = ['somefile.txt', 'anotherfile.txt']

        result = iiqtools_cluster_backup._cleanup_backups(location='/tmp', max_backups=10)
        expected = None

        remove_calls = fake_remove.call_count
        expected_calls = 0

        self.assertEqual(result, expected)
        self.assertEqual(remove_calls, expected_calls)

    @patch.object(iiqtools_cluster_backup.os.path, 'isfile')
    @patch.object(iiqtools_cluster_backup.zipfile, 'is_zipfile')
    @patch.object(iiqtools_cluster_backup.os, 'remove')
    @patch.object(iiqtools_cluster_backup.os, 'listdir')
    def test_backups_equal_max(self, fake_listdir, fake_remove, fake_is_zipfile, fake_isfile):
        """Nothing is deleted if the number of backups found equals the max_backups param"""
        fake_isfile.return_value = True
        fake_is_zipfile.return_value = True
        fake_listdir.return_value = ['insightiq_export_1234567890.zip', 'insightiq_export_2345678901.zip']

        result = iiqtools_cluster_backup._cleanup_backups(location='/tmp', max_backups=2)
        expected = None

        remove_calls = fake_remove.call_count
        expected_calls = 0

        self.assertEqual(result, expected)
        self.assertEqual(remove_calls, expected_calls)

    @patch.object(iiqtools_cluster_backup.os.path, 'isfile')
    @patch.object(iiqtools_cluster_backup.zipfile, 'is_zipfile')
    @patch.object(iiqtools_cluster_backup.os, 'remove')
    @patch.object(iiqtools_cluster_backup.os, 'listdir')
    def test_deletes_oldest(self, fake_listdir, fake_remove, fake_is_zipfile, fake_isfile):
        """Oldest backups are deleted"""
        fake_isfile.return_value = True
        fake_is_zipfile.return_value = True
        fake_listdir.return_value = ['insightiq_export_1234567890.zip', 'insightiq_export_2345678901.zip']

        iiqtools_cluster_backup._cleanup_backups(location='/tmp', max_backups=1)

        the_args, the_kwargs = fake_remove.call_args
        removed_path = the_args[0]
        expexted_args = '/tmp/insightiq_export_1234567890.zip'

        self.assertEqual(removed_path, expexted_args)

    @patch.object(iiqtools_cluster_backup, 'printerr')
    @patch.object(iiqtools_cluster_backup.os.path, 'isfile')
    @patch.object(iiqtools_cluster_backup.zipfile, 'is_zipfile')
    @patch.object(iiqtools_cluster_backup.os, 'remove')
    @patch.object(iiqtools_cluster_backup.os, 'listdir')
    def test_logs_failure(self, fake_listdir, fake_remove, fake_is_zipfile, fake_isfile, fake_printerr):
        """Logs failure to delete old backup"""
        fake_isfile.return_value = True
        fake_is_zipfile.return_value = True
        fake_listdir.return_value = ['insightiq_export_1234567890.zip', 'insightiq_export_2345678901.zip']
        fake_remove.side_effect = RuntimeError('Testing')

        iiqtools_cluster_backup._cleanup_backups(location='/tmp', max_backups=1)

        failures_logged = fake_printerr.call_count
        expected_logged = 1

        self.assertEqual(failures_logged, expected_logged)


class TestClusterBackupGetClusters(unittest.TestCase):
    """A suite of test cases for the get_clusters_in_iiq function"""

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.patcher = patch.object(iiqtools_cluster_backup.iiq_api, 'make_request')
        cls.fake_make_request = cls.patcher.start()
        cls.fake_response = {'clusters' : [{'name': 'myCluster', 'guid': '1234'},
                                          {'name': 'myOtherCluster', 'guid': '5678'}]}
        cls.fake_make_request.return_value = StringIO.StringIO(json.dumps(cls.fake_response))

    @classmethod
    def tearDown(cls):
        """Runs after every test case"""
        cls.patcher.stop()
        cls.fake_make_request = None

    def test_get_clusters_in_iiq(self):
        """Returns a mapping of cluster name to cluster guid"""
        result = iiqtools_cluster_backup.get_clusters_in_iiq()
        expected = {u'myCluster': u'1234', u'myOtherCluster': u'5678'}

        self.assertEqual(result, expected)


class TestClusterBackupClusterOutput(unittest.TestCase):
    """A suite of tests for the format_cluster_output function"""

    def test_format_cluster_output(self):
        clusters = {'myCluster' : '1234'}

        output = iiqtools_cluster_backup.format_cluster_output(clusters)
        expected = '\nClusters monitored by InsightIQ\n-------------------------------\n\n  myCluster'

        self.assertEqual(output, expected)


class TestClusterBackupClustersOk(unittest.TestCase):
    """A suite of tests for the supplied_clusters_ok function"""

    def test_no_intersect(self):
        """supplied_clusters_ok returns False when supplied clusters doesn't intersect available clusters"""
        supplied = ['someCluster', 'anotherCluster']
        available = ['myCluster', 'myOtherCluster']

        result = iiqtools_cluster_backup.supplied_clusters_ok(supplied, available)

        self.assertFalse(result)

    def test_ok(self):
        """supplied_clusters_ok returns True when supplied clusters is a subset available clusters"""
        supplied = ['myCluster']
        available = ['myCluster', 'myOtherCluster']

        result = iiqtools_cluster_backup.supplied_clusters_ok(supplied, available)

        self.assertTrue(result)

    def test_extras(self):
        """supplied_clusters_ok returns False when supplied clusters contains an unknown cluster"""
        supplied = ['myCluster', 'someCluster']
        available = ['myCluster', 'myOtherCluster']

        result = iiqtools_cluster_backup.supplied_clusters_ok(supplied, available)

        self.assertFalse(result)


class TestClusterBackupMakeParams(unittest.TestCase):
    """A suite of tests for the _make_export_params function"""

    def test_nfs_export(self):
        """_make_export_params correctly determines if the export location is NFS based"""
        supplied = ['myCluster']
        available = {'myCluster': '1234'}
        location = 'some-nfs-server:/mnt/data'

        output = iiqtools_cluster_backup._make_export_params(supplied, available, location)
        expected = Parameters(nfs_host='some-nfs-server', location='/mnt/data', guid='1234')

        self.assertEqual(output, expected)

    def test_local_filesystem(self):
        """_make_export_params correctly handles local file system locations for the export"""
        supplied = ['myCluster']
        available = {'myCluster' : '1234'}
        location = '/some/dir'

        output = iiqtools_cluster_backup._make_export_params(supplied, available, location)
        expected = Parameters(nfs_host='', location='/some/dir', guid='1234')

        self.assertEqual(output, expected)


class TestClusterBackupExport(unittest.TestCase):
    """A suite of tests for the export_via_api function"""

    supplied = ['myCluster']
    available = {'myCluster' : '1234'}
    location = '/some/dir'
    username = 'pat'
    password = 'a'

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.patcher = patch.object(iiqtools_cluster_backup, 'InsightiqApi')
        cls.fake_InsightiqApi = cls.patcher.start()

    @classmethod
    def tearDown(cls):
        """Runs after every test case"""
        cls.patcher.stop()
        cls.fake_InsightiqApi = None

    def test_insightiq_api(self):
        """export_via_api uses insightiq_api to make privledged API call"""
        output = iiqtools_cluster_backup.export_via_api(self.supplied,
                                                        self.available,
                                                        self.location,
                                                        self.username,
                                                        self.password)
        self.fake_InsightiqApi.assert_called()


class TestFormatInspectOutput(unittest.TestCase):
    """A suite of tests for the ``_format_inspect_output`` function"""

    def test_output(self):
        """TODO"""
        info = {'isi01': 1234, 'isi02': 12341234}

        result = iiqtools_cluster_backup._format_inspect_output(info)
        expected = ' Name  |  Bytes  \n-----------------\n isi01 |     1234\n isi02 | 12341234\n\n'

        self.assertEqual(result, expected)


class TestClusterBackupMain(unittest.TestCase):
    """A suite of tests for the main function in iiqtools_cluster_backup"""

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.patch_InsightiqApi = patch.object(iiqtools_cluster_backup, 'InsightiqApi')
        cls.fake_InsightiqApi = cls.patch_InsightiqApi.start()
        cls.patch_print = patch.object(iiqtools_cluster_backup, 'print')
        cls.fake_print = cls.patch_print.start()
        cls.patch_printerr = patch.object(iiqtools_cluster_backup, 'printerr')
        cls.fake_printerr = cls.patch_printerr.start()
        cls.patch_iiq_api = patch.object(iiqtools_cluster_backup.iiq_api, 'make_request')
        cls.fake_make_request = cls.patch_iiq_api.start()
        cls.fake_response = {'clusters' : [{'name': 'myCluster', 'guid': '1234'},
                                          {'name': 'myOtherCluster', 'guid': '5678'}]}
        cls.fake_make_request.return_value = StringIO.StringIO(json.dumps(cls.fake_response))
        cls.patch_export = patch.object(iiqtools_cluster_backup, 'export_via_api')
        cls.fake_export = cls.patch_export.start()


    @classmethod
    def tearDown(cls):
        """Runs after every test case"""
        cls.patch_InsightiqApi.stop()
        cls.fake_InsightiqApi = None
        cls.patch_printerr.stop()
        cls.fake_printerr = None
        cls.patch_iiq_api.stop()
        cls.fake_iiq_api = None
        cls.patch_print.stop()
        cls.fake_print = None
        cls.patch_export.stop()
        cls.fake_export = None

    def test_show_clusters(self):
        """Showing clusters returns exit code 0"""
        cli_args = ['--show-clusters']

        exit_code = iiqtools_cluster_backup.main(cli_args)
        expected = 0

        self.assertEqual(exit_code, expected)

    def test_supplied_clusters_not_ok(self):
        """Trying to export junk clusters returns exit code 2"""
        cli_args = ['--clusters', 'someJunkCluster', '--location', '/some/dir', '--username', 'pat', '--password', 'a']

        exit_code = iiqtools_cluster_backup.main(cli_args)
        expected = 2

        self.assertEqual(exit_code, expected)

    def test_connection_error(self):
        """If unable to establish a session with the IIQ API, we return exit code 4"""
        self.fake_export.side_effect = [ConnectionError('testing')]
        cli_args = ['--clusters', 'myCluster', '--location', '/some/dir', '--username', 'pat', '--password', 'a']

        exit_code = iiqtools_cluster_backup.main(cli_args)
        expected = 4

        self.assertEqual(exit_code, expected)

    def test_html_response(self):
        """The IIQ API returns HTML if the API call utterly fails, and we return exit code 3"""
        self.fake_export.side_effect = [ValueError('testing')]
        cli_args = ['--clusters', 'myCluster', '--location', '/some/dir', '--username', 'pat', '--password', 'a']

        exit_code = iiqtools_cluster_backup.main(cli_args)
        expected = 3

        self.assertEqual(exit_code, expected)

    def test_failed_response(self):
        """When the IIQ API rejects our request, we return exit code 5"""
        self.fake_export.return_value = {'msg' : "testing", 'success' : False}
        cli_args = ['--clusters', 'myCluster', '--location', '/some/dir', '--username', 'pat', '--password', 'a']

        exit_code = iiqtools_cluster_backup.main(cli_args)
        expected = 5

        self.assertEqual(exit_code, expected)

    def test_ok_response(self):
        """When the IIQ API accepts the request, we return exit code 0"""
        self.fake_export.return_value = {'msg' : "testing", 'success' : True}
        cli_args = ['--clusters', 'myCluster', '--location', '/some/dir', '--username', 'pat', '--password', 'a']

        exit_code = iiqtools_cluster_backup.main(cli_args)
        expected = 0

        self.assertEqual(exit_code, expected)


if __name__ == '__main__':
    unittest.main()
