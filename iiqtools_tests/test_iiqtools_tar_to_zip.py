# -*- coding: UTF-8 -*-
"""
Unit tests for the ``iiqtools.iiqtools_tar_to_zip`` module's business logic
"""
import os
import unittest
from mock import patch, MagicMock

from iiqtools import iiqtools_tar_to_zip


class TestBufferedZipFile(unittest.TestCase):
    """A suite of tests for the BufferedZipFile class"""

    def setUp(self):
        """Runs before every test case"""
        self.filepath = '/tmp/foo.zip'
        self.zipfile = iiqtools_tar_to_zip.BufferedZipFile('/tmp/foo.zip', mode='w')
        self.zipfile.fp = MagicMock()
        self.zipfile._writecheck = MagicMock()

        self.fake_file = MagicMock()
        self.fake_file.read.side_effect = ['asdf', '']

    def tearDown(self):
        """Runs after every tests case"""
        os.remove(self.filepath)

    @patch.object(iiqtools_tar_to_zip, 'struct')
    @patch.object(iiqtools_tar_to_zip, 'binascii')
    def test_basic(self, fake_binascii, fake_struct):
        """BufferedZipFile - writebuffered is callable"""
        self.zipfile.writebuffered(filename='foo', file_handle=self.fake_file)


class TestCheckTar(unittest.TestCase):
    """A suite of tests for the check_tar function"""

    @patch.object(iiqtools_tar_to_zip.os.path, 'isfile')
    @patch.object(iiqtools_tar_to_zip.tarfile, 'is_tarfile')
    def test_valid_tar(self, fake_is_tarfile, fake_isfile):
        """The supplied tar value is returned when it's a valid tar file"""
        fake_is_tarfile.return_value = True
        fake_isfile.return_value = True

        sent = 'insightiq_export_1234567890.tar.gz'
        returned = iiqtools_tar_to_zip.check_tar(sent)

        self.assertEqual(sent, returned)

    def test_not_a_file(self):
        """argparse.ArgumentTypeError is raised if the supplied tar file doesn't exist"""
        sent = 'insightiq_export_1234567890.tar.gz'
        self.assertRaises(iiqtools_tar_to_zip.argparse.ArgumentTypeError, iiqtools_tar_to_zip.check_tar, sent)

    @patch.object(iiqtools_tar_to_zip.os.path, 'isfile')
    @patch.object(iiqtools_tar_to_zip.tarfile, 'is_tarfile')
    def test_not_a_tar(self, fake_is_tarfile, fake_isfile):
        """argparse.ArgumentTypeError is raised if the supplied file isn't a tar file"""
        fake_isfile.return_value = True
        fake_is_tarfile.return_value = False
        sent = 'insightiq_export_1234567890.tar.gz'
        self.assertRaises(iiqtools_tar_to_zip.argparse.ArgumentTypeError, iiqtools_tar_to_zip.check_tar, sent)

    @patch.object(iiqtools_tar_to_zip.os.path, 'isfile')
    @patch.object(iiqtools_tar_to_zip.tarfile, 'is_tarfile')
    def test_bad_file_name(self, fake_is_tarfile, fake_isfile):
        """argparse.ArgumentTypeError is raised if the tar file doesn't adhere to the expected naming convention"""
        fake_is_tarfile.return_value = True
        fake_isfile.return_value = True

        sent = 'insightiq_export_1.tar.gz'
        self.assertRaises(iiqtools_tar_to_zip.argparse.ArgumentTypeError, iiqtools_tar_to_zip.check_tar, sent)


class TestParseCli(unittest.TestCase):
    """A suite of tests for the parse_cli function"""

    # Mocking away stderr to avoid spam in output while running tests
    @patch.object(iiqtools_tar_to_zip.argparse._sys, 'stderr')
    def test_no_args(self, fake_stderr):
        """When no cli args are given, SystemExit is raised"""
        self.assertRaises(SystemExit, iiqtools_tar_to_zip.parse_cli, [])

    @patch.object(iiqtools_tar_to_zip.argparse._sys, 'stderr')
    def test_missing_required(self, fake_stderr):
        """When missing required args, SystemExit is raised"""
        self.assertRaises(SystemExit, iiqtools_tar_to_zip.parse_cli, ['-o', '/tmp'])

    @patch.object(iiqtools_tar_to_zip, 'check_tar')
    @patch.object(iiqtools_tar_to_zip, 'check_path')
    def test_returns_namespace(self, fake_check_path, fake_check_tar):
        fake_check_path.return_value = '/tmp'
        fake_check_tar.return_value = 'insightiq_export_1234.tar.gz'

        args = iiqtools_tar_to_zip.parse_cli(['--source-tar', 'insightiq_export_1234.tar.gz', '--output-dir', '/tmp'])

        self.assertTrue(isinstance(args, iiqtools_tar_to_zip.argparse.Namespace))


class TestGetTimestampFromExport(unittest.TestCase):
    """A suite of tests for the get_timestamp_from_export function"""

    def test_absolute_path(self):
        """get_timestamp_from_export works if source_tar is a file path"""
        source_tar = '/datastore/insightiq_export_1234.tar.gz'

        actual = iiqtools_tar_to_zip.get_timestamp_from_export(source_tar)
        expected = '1234'

        self.assertEqual(actual, expected)


class TestJoinname(unittest.TestCase):
    """A suite of tests for the joinname function"""

    def test_relative_path(self):
        """joinname - works with relative paths"""
        the_dir = 'insightiq_export_1234567890'
        the_file = '../somefile'

        actual = iiqtools_tar_to_zip.joinname(the_dir, the_file)
        expected = 'insightiq_export_1234567890/somefile'

        self.assertEqual(actual, expected)

    def test_absolute_path(self):
        """joinname - works with absolute paths"""
        the_dir = 'insightiq_export_1234567890'
        the_file = '/datastore/somefile'

        actual = iiqtools_tar_to_zip.joinname(the_dir, the_file)
        expected = 'insightiq_export_1234567890/somefile'

        self.assertEqual(actual, expected)


class TestMain(unittest.TestCase):
    """A suite of tests for the main function"""

    def setUp(self):
        """Runs before every test case"""
        # So we don't have to patch the same stuff in every test case
        self.patches = {'fake_logger' : patch('iiqtools.iiqtools_tar_to_zip.get_logger'),
                        'fake_BufferedZipFile' : patch('iiqtools.iiqtools_tar_to_zip.BufferedZipFile'),
                        'fake_parse_cli' : patch('iiqtools.iiqtools_tar_to_zip.parse_cli'),
                        'fake_tarfile' : patch('iiqtools.iiqtools_tar_to_zip.tarfile'),
                        'fake_os_remove' : patch('iiqtools.iiqtools_tar_to_zip.os.remove'),
                       }
        for patch_name, the_patch in self.patches.items():
            patched_obj = the_patch.start()
            setattr(self, patch_name, patched_obj)

        self.fake_parse_cli.source_tar = 'insightiq_export_1234567890.tar.gz'
        self.fake_parse_cli.output_dir = '/tmp'
        fake_file1 = MagicMock()
        fake_file1.name = 'foo'
        fake_file2 = MagicMock()
        fake_file2.name = 'bar'
        self.fake_tarfile.open.return_value.getmembers.return_value = [fake_file1, fake_file2]

    def tearDown(self):
        """Runs after every test case"""
        for the_patch in self.patches.values():
            the_patch.stop()

    def test_basic(self):
        """The main function returns zero when there are no errors"""
        exit_code = iiqtools_tar_to_zip.main(['-s', 'insightiq_export_1234567890.tar.gz', '-o', '/tmp'])
        self.assertEqual(exit_code, 0)

    def test_zip_creation_failure(self):
        """The main function returns 1 when it cannot create the new zip file"""
        self.fake_BufferedZipFile.side_effect = [IOError()]
        exit_code = iiqtools_tar_to_zip.main(['-s', 'insightiq_export_1234567890.tar.gz', '-o', '/tmp'])

        self.assertEqual(exit_code, 1)

    def test_mid_write_failure(self):
        """
        The main function returns the error code of the exception if it fails
        while writing to the new zip file
        """
        self.fake_BufferedZipFile.return_value.writebuffered.side_effect = [IOError(13, 'testing', 'some_file')]
        exit_code = iiqtools_tar_to_zip.main(['-s', 'insightiq_export_1234567890.tar.gz', '-o', '/tmp'])

        self.assertEqual(exit_code, 13)
        self.assertTrue(self.fake_os_remove.called)


if __name__ == '__main__':
    unittest.main()
