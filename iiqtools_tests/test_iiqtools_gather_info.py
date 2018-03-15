# -*- coding: UTF-8 -*-
"""
Unit tests for the iiqtools.iiqtools_gather_info logic
"""
import os
import json
import gzip
import glob
import unittest
import argparse
import __builtin__

from mock import patch, MagicMock

from iiqtools import iiqtools_gather_info
from iiqtools.utils.versions import Version


class TestGetTarfile(unittest.TestCase):
    """A suite of test cases for the iiqtools_gather_info.get_tarfile function"""

    def setUp(self):
        """Runs before every test case"""
        self.output_dir = '/tmp'
        self.case_number = 1
        self.the_time = 1234

    def tearDown(self):
        """Runs after every test case"""
        test_files = glob.glob('/tmp/IIQLogs*')
        for the_file in test_files:
            os.remove(the_file)

    def test_get_tarfile_name(self):
        """The `get_tarfile` function returns the expected file"""
        the_tarfile = iiqtools_gather_info.get_tarfile(self.output_dir,
                                                  self.case_number,
                                                  the_time=self.the_time)
        tarfile_name = the_tarfile.name
        expected_name = '%s/IIQLogs-sr%s-%s.tgz' % (self.output_dir,
                                                        self.case_number,
                                                        self.the_time)

        self.assertEqual(tarfile_name, expected_name)

    def test_get_tarfile_is_compressed(self):
        """The `get_tarfile` function returns a gzipped file"""
        the_tarfile = iiqtools_gather_info.get_tarfile(self.output_dir,
                                                  self.case_number)

        self.assertTrue(isinstance(the_tarfile.fileobj, gzip.GzipFile))



class TestAddFromMemory(unittest.TestCase):
    """A suite of tests for the iiqtools_gather_info.add_from_memory function"""

    def setUp(self):
        """Runs before every test case"""
        self.fake_tarfile = MagicMock()

    def test_add_from_memory_addfile(self):
        """The add_from_memory function adds the data to the tar file"""

        iiqtools_gather_info.add_from_memory(the_tarfile=self.fake_tarfile,
                                        data_name='foo.json',
                                        data='{"some" : "json string"}')
        call_count = self.fake_tarfile.addfile.call_count
        expected = 1

        self.assertEqual(call_count, expected)

    @patch.object(iiqtools_gather_info.tarfile, 'TarInfo')
    def test_add_from_memory_mode(self, fake_tarinfo):
        """The add_from_memory fuction sets the correct POSIX permissions"""
        fake_info = MagicMock()
        fake_tarinfo.return_value = fake_info
        iiqtools_gather_info.add_from_memory(the_tarfile=self.fake_tarfile,
                                        data_name='foo.json',
                                        data='{"some" : "json string"}')
        posix_oct = fake_info.mode
        expected = 292 # that's 444 POSIX in decimal

        self.assertEqual(posix_oct, expected)


class TestParseCli(unittest.TestCase):
    """A suite of test cases for the parse_cli function"""

    def test_returns_namespace(self):
        """Supplying all required args to iiqtools_gather_info.parse_cli returns a namespace object"""
        sent_args = ['--output-dir', '/tmp', '--case-number', '2']
        out_args = iiqtools_gather_info.parse_cli(sent_args)

        self.assertTrue(isinstance(out_args, argparse.Namespace))

    # Mocking away stderr to avoid spam in output while running tests
    @patch.object(iiqtools_gather_info.argparse._sys, 'stderr')
    def test_no_args(self, fake_stderr):
        """Passing zero args to iiqtools_gather_info.parse_cli raises SystemExit"""
        sent_args = []
        self.assertRaises(SystemExit, iiqtools_gather_info.parse_cli, sent_args)

    @patch.object(iiqtools_gather_info.argparse._sys, 'stderr')
    def test_only_output_dir(self, fake_stderr):
        """Supplying only --output-dir raises SystemExit"""
        sent_args = ['--output-dir', '/tmp',]
        self.assertRaises(SystemExit, iiqtools_gather_info.parse_cli, sent_args)

    @patch.object(iiqtools_gather_info.argparse._sys, 'stderr')
    def test_only_case_number(self, fake_stderr):
        """Supplying only --case-number raises SystemExit"""
        sent_args = ['--case-number', '1',]
        self.assertRaises(SystemExit, iiqtools_gather_info.parse_cli, sent_args)


class TestCallIiqApi(unittest.TestCase):
    """A suite of test cases for the call_iiq_api function"""

    def setUp(self):
        """Runs before every test case"""
        # InsightIQ is closed source, so in the lib we replace the iiq_api
        # function (which we cannot import) with a mock object
        iiqtools_gather_info.iiq_api = MagicMock()
        self.fake_response = MagicMock()
        self.fake_response.read.return_value = '{"foo":"bar"}'
        iiqtools_gather_info.iiq_api.make_request.return_value = self.fake_response

    def test_response_is_json(self):
        """The response is seralized, valid JSON"""
        response = iiqtools_gather_info.call_iiq_api(uri='/foo')
        deseralized = json.loads(response)

        self.assertTrue(isinstance(response, str))
        self.assertTrue(isinstance(deseralized, dict))
        self.assertEqual(deseralized['response'], {'foo' : 'bar'})

    def test_api_error(self):
        """The response object notes if the IIQ API failed"""
        iiqtools_gather_info.iiq_api.make_request.side_effect = [RuntimeError('testing')]

        response = iiqtools_gather_info.call_iiq_api(uri='/foo')
        data = json.loads(response)
        err_msg = 'unable to query InsightIQ API'

        self.assertEqual(err_msg, data['error'])

    def test_notes_tracebacks(self):
        """Unexpected exceptions have the assocated traceback logged in the response"""
        # So we can A) fix it, and B) write a unit test for it! :D
        iiqtools_gather_info.iiq_api.make_request.side_effect = [Exception('testing')]

        response = iiqtools_gather_info.call_iiq_api(uri='/foo')
        data = json.loads(response)
        err_msg = 'testing'

        self.assertEqual(err_msg, data['error'])
        self.assertTrue(data['traceback'].startswith('Traceback'))


class TestIiqApiHelpers(unittest.TestCase):
    """A suite of test cases for the helper functions that pull
       data from the InsightIQ API
    """

    def setUp(self):
        """Runs before every test case"""
        # InsightIQ is closed source, so in the lib we replace the iiq_api
        # function (which we cannot import) with a mock object
        iiqtools_gather_info.iiq_api = MagicMock()
        self.fake_response = MagicMock()
        self.fake_response.read.return_value = '{"foo":"bar"}'
        iiqtools_gather_info.iiq_api.make_request.return_value = self.fake_response

    def test_datastore_info(self):
        """Function `datastore_info` calls the correct API endpoint"""
        data = iiqtools_gather_info.datastore_info()
        the_json = json.loads(data)
        expected_endpoint = '/api/datastore/usage?current_dir=true'

        self.assertEqual(the_json['endpoint'], expected_endpoint)

    def test_clusters_info(self):
        """Function `clusters_info` calls the correct API endpoint"""
        data = iiqtools_gather_info.clusters_info()
        the_json = json.loads(data)
        expected_endpoint = '/api/clusters'

        self.assertEqual(the_json['endpoint'], expected_endpoint)

    def test_ldap_info(self):
        """Function `ldap_info` calls the correct API endpoint"""
        data = iiqtools_gather_info.ldap_info()
        the_json = json.loads(data)
        expected_endpoint = '/api/ldap/configs'

        self.assertEqual(the_json['endpoint'], expected_endpoint)

    def test_reports_info(self):
        """Function `reports_info` calls the correct API endpoint"""
        data = iiqtools_gather_info.reports_info()
        the_json = json.loads(data)
        expected_endpoint = '/api/reports'

        self.assertEqual(the_json['endpoint'], expected_endpoint)


class TestCliCmdInfo(unittest.TestCase):
    """A suite of tests for the cli_cmd_info function"""

    def test_might_fail(self):
        """Verify that cli_cmd_info works without mocks"""
        # the `free -m` command is most likely on every system, thus most likely to work
        data = iiqtools_gather_info.cli_cmd_info('free -m', iiqtools_gather_info.cli_parsers.memory_to_dict)
        the_json = json.loads(data)
        expected_cmd = 'free -m'

        self.assertEqual(the_json['command'], expected_cmd)

    def test_bad_command(self):
        """Supplying a bad CLI command to `cli_cmd_info` returns valid JSON still"""
        data = iiqtools_gather_info.cli_cmd_info('sdfwehsxiodaweh', iiqtools_gather_info.cli_parsers.memory_to_dict)
        the_json = json.loads(data)

        self.assertTrue(the_json['exitcode'] != 0)

    def test_parser_failure(self):
        """A good command, and parser failure still generates valid JSON"""
        data = iiqtools_gather_info.cli_cmd_info('date', iiqtools_gather_info.cli_parsers.memory_to_dict)
        the_json = json.loads(data)

        self.assertTrue(the_json['traceback'].startswith('Traceback'))


class TestCliCmdInfoHelpers(unittest.TestCase):
    """A suite of tests for the helpers for obtaining CLI command output"""

    @patch.object(iiqtools_gather_info, 'cli_cmd_info')
    def test_mount_info(self, fake_cli_cmd_info):
        """iiqtools_gather_info.mount_info calls the expected command"""
        iiqtools_gather_info.mount_info()
        args, _ = fake_cli_cmd_info.call_args
        sent_command = args[0]
        expected_command = 'df -P'

        self.assertEqual(sent_command, expected_command)

    @patch.object(iiqtools_gather_info, 'cli_cmd_info')
    def test_memory_info(self, fake_cli_cmd_info):
        """iiqtools_gather_info.memory_info calls the expected command"""
        iiqtools_gather_info.memory_info()
        args, _ = fake_cli_cmd_info.call_args
        sent_command = args[0]
        expected_command = 'free -m'

        self.assertEqual(sent_command, expected_command)

    @patch.object(iiqtools_gather_info, 'cli_cmd_info')
    def test_ifconfig_info(self, fake_cli_cmd_info):
        """iiqtools_gather_info.ifconfig_info calls the expected command"""
        iiqtools_gather_info.ifconfig_info()
        args, _ = fake_cli_cmd_info.call_args
        sent_command = args[0]
        expected_command = 'ifconfig'

        self.assertEqual(sent_command, expected_command)

    @patch.object(iiqtools_gather_info, 'versions')
    def test_iiq_version_info(self, fake_versions):
        """iiqtools_gather_info.iiq_version_info calls the expected command"""
        fake_versions.get_iiq_version.return_value = Version(version='1.2.3', name='InsightIQ')
        fake_versions.get_iiqtools_version.return_value = Version(version='1.2.3', name='InsightIQ')
        data = iiqtools_gather_info.iiq_version_info()
        expected = {'insightiq' : '1.2.3', 'iiqtools' : '1.2.3'}

        self.assertEqual(json.loads(data), expected)

class TestIiqGatheInfoMain(unittest.TestCase):
    """A suite of tests for the iiqtools_gather_info.main function"""

    @patch.object(iiqtools_gather_info, 'versions')
    @patch.object(iiqtools_gather_info.sys, 'stdout')
    @patch.object(__builtin__, 'raw_input')
    @patch.object(iiqtools_gather_info, 'get_tarfile')
    @patch.object(iiqtools_gather_info, 'get_logger')
    def test_main(self, fake_get_logger, fake_get_tarfile, fake_raw_input, fake_stdout, fake_versions):
        """iiqtools_gather_info.main is callable, and returns an integer"""
        fake_versions.get_iiq_version.return_value = Version(version='1.2.3', name='InsightIQ')
        fake_versions.get_iiqtools_version.return_value = Version(version='1.2.3', name='InsightIQ')
        fake_raw_input.return_value = 'yes'
        exit_code = iiqtools_gather_info.main(['--case-number', '0', '--output-dir', '/tmp'])
        expected = 0

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_gather_info.sys, 'stdout')
    @patch.object(__builtin__, 'raw_input')
    @patch.object(iiqtools_gather_info, 'get_tarfile')
    @patch.object(iiqtools_gather_info, 'get_logger')
    def test_not_root_and_no(self, fake_get_logger, fake_get_tarfile, fake_raw_input, fake_stdout):
        """If not ran as root, and you say `no` to the prompt, the script exit code is 1"""
        fake_raw_input.return_value = 'no'
        exit_code = iiqtools_gather_info.main(['--case-number', '0', '--output-dir', '/tmp'])
        expected = 1

        self.assertEqual(exit_code, expected)


    @patch.object(iiqtools_gather_info.sys, 'stdout')
    @patch.object(__builtin__, 'raw_input')
    @patch.object(iiqtools_gather_info, 'get_tarfile')
    @patch.object(iiqtools_gather_info, 'get_logger')
    def test_ioerror(self, fake_get_logger, fake_get_tarfile, fake_raw_input, fake_stdout):
        """An I/O (or OS) error when creating the tarfile returns a non-zero exit code"""
        fake_raw_input.return_value = 'yes'
        fake_get_tarfile.side_effect = [IOError(13, 'testing', 'some_file')]

        exit_code = iiqtools_gather_info.main(['--case-number', '0', '--output-dir', '/tmp'])
        expected = 13

        self.assertEqual(exit_code, expected)


if __name__ == '__main__':
    unittest.main()
