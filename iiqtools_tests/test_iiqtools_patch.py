# -*- coding: UTF-8 -*-
"""
A suite of tests for the iiqtools_patch module
"""
import __builtin__
import unittest
from collections import namedtuple
from mock import patch, MagicMock, mock_open

from iiqtools import iiqtools_patch
from iiqtools.utils import versions


class TestDataStructures(unittest.TestCase):
    """A set of test cases for the data structures used by iiqtools_patch"""

    def test_patch_contents(self):
        """The PatchContents API accepts the expected params"""
        patch_contents = iiqtools_patch.PatchContents(readme='some readme data',
                                                 meta_ini='the contents of meta.ini',
                                                 patched_files={'/patched/file' : '/original/file/location'})

        self.assertTrue(isinstance(patch_contents, iiqtools_patch._PatchContents))

    @patch.object(iiqtools_patch, 'tarfile')
    def test_extract_patch_contents_returns(self, fake_tarfile):
        """iiqtools_patch.extract_patch_contents returns an instance of PatchContents"""
        fake_log = MagicMock()
        fake_tar = MagicMock()
        fake_tarfile.open.return_value = fake_tar
        patch_contents = iiqtools_patch.extract_patch_contents('/bogus-patch.tgz', fake_log)

        self.assertTrue(isinstance(patch_contents, iiqtools_patch._PatchContents))

    @patch.object(iiqtools_patch, 'tarfile')
    def test_extract_patch_contents(self, fake_tarfile):
        """iiqtools_patch.extract_patch_contents populates PatchContents when patch file is valid"""
        fake_log = MagicMock()
        fake_tar = MagicMock()
        fake_tar.extractfile.return_value.read.return_value = 'some data'
        fake_tar.getmembers.return_value = [self.fake_item_factory('/some/path', isdir=True),
                                            self.fake_item_factory('meta.ini', isdir=False),
                                            self.fake_item_factory('README.txt', isdir=False),
                                            self.fake_item_factory('/patched/file', isdir=False)]
        fake_tarfile.open.return_value = fake_tar
        patch_contents = iiqtools_patch.extract_patch_contents('/bogus-patch.tgz', fake_log)

        self.assertTrue(isinstance(patch_contents, iiqtools_patch._PatchContents))
        self.assertEqual(patch_contents.readme, 'some data')
        self.assertEqual(patch_contents.meta_ini, 'some data')
        self.assertEqual(patch_contents.patched_files, {'/patched/file' : 'some data'})


    def fake_item_factory(self, path, isdir=False):
        """Simplifies making fake items within a tarfile"""
        fake_item = MagicMock()
        fake_item.isdir.return_value = isdir
        fake_item.path = path
        return fake_item


class TestValidators(unittest.TestCase):
    """A suite of test cases for the different validators in iiqtools_patch"""

    @patch.object(iiqtools_patch.tarfile, 'is_tarfile')
    def test_check_file_not_tar(self, fake_is_tarfile):
        """iiqtools_patch.check_file raises argparse.ArgumentTypeError if file isn't a tarfile"""
        fake_is_tarfile.return_value = False

        self.assertRaises(iiqtools_patch.argparse.ArgumentTypeError, iiqtools_patch.check_file, 'somefile.txt')

    @patch.object(iiqtools_patch.tarfile, 'is_tarfile')
    def test_check_file_ioerror(self, fake_is_tarfile):
        """iiqtools_patch.check_file raises argparse.ArgumentTypeError if the value isn't a real file"""
        fake_is_tarfile.side_effect = IOError(9001, 'testerror', 'somefile')

        expected = 'testerror: somefile'
        try:
            iiqtools_patch.check_file('somefile')
        except iiqtools_patch.argparse.ArgumentTypeError as doh:
            result = '%s' % doh
        else:
            result = 'Failed'

        self.assertEqual(expected, result)

    @patch.object(iiqtools_patch.tarfile, 'is_tarfile')
    def test_check_file_ok(self, fake_is_tarfile):
        """iiqtools_patch.check_file returns the value if it's valid"""
        fake_is_tarfile.return_value = True

        expected = 'somefile'
        result = iiqtools_patch.check_file('somefile')

        self.assertEqual(expected, result)

    def test_parse_cli_ok(self):
        """iiqtools_patch.parse_cli returns argparse.Namespace for valid input"""
        args = iiqtools_patch.parse_cli(['--show'])
        self.assertTrue(isinstance(args, iiqtools_patch.argparse.Namespace))

    def test_parse_cli_show(self):
        """iiqtools_patch.parse_cli the --show arg can accept a value"""
        args = iiqtools_patch.parse_cli(['--show', 'patch1234'])

        self.assertEqual(args.show, 'patch1234')

    def test_patch_is_valid_ok(self):
        """iiqtools_patch.patch_is_valid returns True when all checks are OK"""
        fake_logger = MagicMock()
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='[info]\nname=patch1234\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        result = iiqtools_patch.patch_is_valid(patch_contents, fake_logger)
        self.assertTrue(result)

    def test_patch_is_valid_leading_slash(self):
        """iiqtools_patch.patch_is_valid returns False if the patch file location starts from root"""
        fake_logger = MagicMock()
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='[info]\nname=patch1234\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\n/some/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        result = iiqtools_patch.patch_is_valid(patch_contents, fake_logger)
        self.assertFalse(result)

    def test_patch_is_valid_no_files(self):
        """iiqtools_patch.patch_is_valid returns False if there are no files defined in patch"""
        fake_logger = MagicMock()
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='[info]\nname=patch1234\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]',
                                                 patched_files={'some/file.py' : 'data'})
        result = iiqtools_patch.patch_is_valid(patch_contents, fake_logger)
        self.assertFalse(result)

    def test_patch_is_valid_missing_min_max_versions(self):
        """iiqtools_patch.patch_is_valid returns False if minimum and maximum are not defined within the patch"""
        fake_logger = MagicMock()
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='[info]\nname=patch1234\nbug=1234\n[version]\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        result = iiqtools_patch.patch_is_valid(patch_contents, fake_logger)
        self.assertFalse(result)

    def test_patch_is_valid_missing_name_bug(self):
        """iiqtools_patch.patch_is_valid returns False if name and bug is not defined"""
        fake_logger = MagicMock()
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='[info]\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        result = iiqtools_patch.patch_is_valid(patch_contents, fake_logger)
        self.assertFalse(result)

    def test_patch_is_valid_missing_headers(self):
        """iiqtools_patch.patch_is_valid returns False if any expected header is missing in meta.ini"""
        fake_logger = MagicMock()
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='minimum=4.0\nmaximum=4.1.1\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        result = iiqtools_patch.patch_is_valid(patch_contents, fake_logger)
        self.assertFalse(result)

    def test_patch_is_valid_bad_contents(self):
        """iiqtools_patch.patch_is_valid returns False is the supplied PatchContents is missing data"""
        fake_logger = MagicMock()
        patch_contents = iiqtools_patch.PatchContents(readme='',
                                                 meta_ini='',
                                                 patched_files={})
        result = iiqtools_patch.patch_is_valid(patch_contents, fake_logger)
        self.assertFalse(result)

    @patch.object(iiqtools_patch, 'md5_matches')
    def test_source_is_patchable_ok(self, fake_md5_matches):
        """iiqtools_patch.source_is_patchable returns True when all checks complete successfully"""
        fake_logger = MagicMock()
        fake_md5_matches.return_value = True
        iiq_dir = 'some/dir'
        patch_map = {'insightiq/source/file.py' : 'expectedMD5hash'}

        result = iiqtools_patch.source_is_patchable(patch_map, iiq_dir, fake_logger)
        expected = True

        self.assertEqual(result, expected)

    @patch.object(iiqtools_patch, 'md5_matches')
    def test_source_is_patchable_ioerror(self, fake_md5_matches):
        """iiqtools_patch.source_is_patchable returns False if there's an error while reading the source files"""
        fake_logger = MagicMock()
        fake_md5_matches.side_effect = IOError(9001, 'testerror', 'somefile')
        iiq_dir = 'some/dir'
        patch_map = {'insightiq/source/file.py' : 'expectedMD5hash'}

        result = iiqtools_patch.source_is_patchable(patch_map, iiq_dir, fake_logger)
        expected = False

        self.assertEqual(result, expected)

    @patch.object(iiqtools_patch, 'md5_matches')
    def test_source_is_patchable_bad_md5(self, fake_md5_matches):
        """iiqtools_patch.source_is_patchable returns False if the source file md5 doesn't match the expected md5"""
        fake_logger = MagicMock()
        fake_md5_matches.return_value = False
        iiq_dir = 'some/dir'
        patch_map = {'insightiq/source/file.py' : 'expectedMD5hash'}

        result = iiqtools_patch.source_is_patchable(patch_map, iiq_dir, fake_logger)
        expected = False

        self.assertEqual(result, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    def test_versions_ok(self, fake_get_iiq_version):
        """iiqtools_patch.version_ok returns True if the installed version of IIQ is within the min/max of the patch"""
        fake_logger = MagicMock()
        fake_get_iiq_version.return_value = iiqtools_patch.versions.Version(name='iiq', version='4.1.0.0')
        version_info = {'minimum' : '4.0.0.0', 'maximum' : '4.1.1.3'}

        result = iiqtools_patch.version_ok(version_info, fake_logger)
        expected = True

        self.assertEqual(result, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    def test_versions_ok_min(self, fake_get_iiq_version):
        """iiqtools_patch.version_ok returns True the the installed version is equal to the minimum patch version"""
        fake_logger = MagicMock()
        fake_get_iiq_version.return_value = iiqtools_patch.versions.Version(name='iiq', version='4.1.0.0')
        version_info = {'minimum' : '4.1.0.0', 'maximum' : '4.1.1.3'}

        result = iiqtools_patch.version_ok(version_info, fake_logger)
        expected = True

        self.assertEqual(result, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    def test_versions_ok_max(self, fake_get_iiq_version):
        """iiqtools_patch.version_ok returns True the the installed version is equal to the maximum patch version"""
        fake_logger = MagicMock()
        fake_get_iiq_version.return_value = iiqtools_patch.versions.Version(name='iiq', version='4.1.1.3')
        version_info = {'minimum' : '4.1.0.0', 'maximum' : '4.1.1.3'}

        result = iiqtools_patch.version_ok(version_info, fake_logger)
        expected = True

        self.assertEqual(result, expected)

    def test_md5_matches_ok(self):
        """iiqtools_patch.md5_matches returns True when the file content's md5 matches the supplied md5"""
        fake_open = mock_open(read_data='foo')
        fake_logger = MagicMock()
        the_hash = 'acbd18db4cc2f85cedef654fccc4a4d8'

        with patch('iiqtools.iiqtools_patch.open', fake_open, create=True):
            result = iiqtools_patch.md5_matches('some/file.py', the_hash, fake_logger)
        expected = True

        self.assertEqual(result, expected)

    def test_md5_matches_false(self):
        """iiqtools_patch.md5_matches returns False when the file content's md5 does not matches the supplied md5"""
        fake_open = mock_open(read_data='asdfwefwewsd')
        fake_logger = MagicMock()
        the_hash = 'acbd18db4cc2f85cedef654fccc4a4d8'

        with patch('iiqtools.iiqtools_patch.open', fake_open, create=True):
            result = iiqtools_patch.md5_matches('some/file.py', the_hash, fake_logger)
        expected = False

        self.assertEqual(result, expected)

    def test_expected_backups_ok(self):
        """iiqtools_patch.expected_backups returns True if the source file copies found meet the patches expectations"""
        fake_logger = MagicMock()
        found_backups = ['path___to___some_file.py']
        expected_backups = ['path/to/some_file.py']

        result = iiqtools_patch.expected_backups(found_backups, expected_backups, fake_logger)
        expected = True

        self.assertEqual(result, expected)

    def test_expected_backups_duplicates(self):
        """iiqtools_patch.expected_backups returns False if duplicate source file copies are found"""
        fake_logger = MagicMock()
        found_backups = ['path__to__some_file.py', 'path__to__some_file.py']
        expected_backups = ['path/to/some_file.py']

        result = iiqtools_patch.expected_backups(found_backups, expected_backups, fake_logger)
        expected = False

        self.assertEqual(result, expected)

    def test_expected_backups_failure(self):
        """iiqtools_patch.expected_backups returns False if source file copies are don't meet expectations"""
        fake_logger = MagicMock()
        found_backups = ['some_file.py', '']
        expected_backups = ['path/to/some_file.py']

        result = iiqtools_patch.expected_backups(found_backups, expected_backups, fake_logger)
        expected = False

        self.assertEqual(result, expected)

    def test_expected_backups_extra_found(self):
        """iiqtools_patch.expected_backups returns False if extra files are located with the backups"""
        fake_logger = MagicMock()
        found_backups = ['path__to__some_file.py', 'path__to__another_file.py']
        expected_backups = ['path/to/some_file.py']

        result = iiqtools_patch.expected_backups(found_backups, expected_backups, fake_logger)
        expected = False

        self.assertEqual(result, expected)


    def test_expected_backups_missing_copies(self):
        """iiqtools_patch.expected_backups returns False if we don't find all expected backups"""
        fake_logger = MagicMock()
        found_backups = ['path__to__some_file.py']
        expected_backups = ['path/to/some_file.py', 'path/to/other_file.py']

        result = iiqtools_patch.expected_backups(found_backups, expected_backups, fake_logger)
        expected = False

        self.assertEqual(result, expected)


class TestUtils(unittest.TestCase):
    """A suite of test cases for the utility functions within iiqtools_patch"""

    def test_convert_patch_name_to_source(self):
        """"iiqtools_patch.convert_patch_name correctly converts a backup file name to the source path"""
        name = 'some___backup_copy.py'
        expected = 'some/backup_copy.py'
        result = iiqtools_patch.convert_patch_name(name, to='source')

        self.assertEqual(expected, result)

    def test_convert_duner_files_to_backup(self):
        """iiqtools_patch.convert_patch_name handles double-under files, like __init__.py when converting to backup name"""
        name = 'some/__init__.py'
        expected = 'some_____init__.py'
        result = iiqtools_patch.convert_patch_name(name, to='backup')

        self.assertEqual(expected, result)

    def test_convert_duner_files_to_source(self):
        """iiqtools_patch.convert_patch_name handles double-under files, like __init__.py when converting to source name"""
        name = 'some_____init__.py'
        expected = 'some/__init__.py'
        result = iiqtools_patch.convert_patch_name(name, to='source')

        self.assertEqual(expected, result)

    def test_convert_patch_name_to_backup(self):
        """"iiqtools_patch.convert_patch_name correctly converts source file path to a backup file name"""
        name = 'some/backup_copy.py'
        expected = 'some___backup_copy.py'
        result = iiqtools_patch.convert_patch_name(name, to='backup')

        self.assertEqual(expected, result)

    def test_convert_patch_name_value_error(self):
        """iiqtools_patch.convert_patch_name raises ValueError if "to" param is a bad value"""
        self.assertRaises(ValueError, iiqtools_patch.convert_patch_name, name='some_file.py', to='derp')

    def test_patch_backups_path(self):
        """iiqtools_patch.patch_backups_path correctly idenitifes where the backups are stored"""
        # WARNING - if you ever have to modify this test, you are most definitely
        # breaking backwards compatibility with existing patches
        result = iiqtools_patch.patch_backups_path('some/dir')
        expected = 'some/dir/originals'

        self.assertEqual(expected, result)

    def test_join_path(self):
        """iiqtools_patch.join_path joins args with a '/'"""
        result = iiqtools_patch.join_path('some', 'path')
        expected = 'some/path'

        self.assertEqual(result, expected)


class TestCommandHandlers(unittest.TestCase):
    """A suite of test cases for the functions that do most of the work"""

    @patch.object(iiqtools_patch.os, 'remove')
    @patch.object(iiqtools_patch.shutil, 'copyfile')
    @patch.object(iiqtools_patch.os.path, 'isfile')
    def test_restore_originals(self, fake_isfile, fake_copyfile, fake_remove):
        """iiqtools_patch.restore_originals returns None when procedure encounters no issues"""
        fake_isfile.return_value = True
        result = iiqtools_patch.restore_originals(iiq_dir='some/dir', patch_dir='some/dir/patches', backup_files=['the__backup__file.py'])
        expected = None

        self.assertEqual(result, expected)

    @patch.object(iiqtools_patch.shutil, 'copyfile')
    @patch.object(iiqtools_patch.os, 'mkdir')
    def test_install_patch(self, fake_mkdir, fake_copyfile):
        """iiqtools_patch.install_patch returns None when no issues are encounted"""
        fake_logger = MagicMock()
        fake_open = mock_open(read_data='foo')
        patch_contents = iiqtools_patch.PatchContents(readme='readme.txt contents',
                                                 meta_ini='foo',
                                                 patched_files={'/some/patched/files.py' : 'data in patched file'})
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=False,
                                         readme='the readme contents',
                                         specific_patch='patch1234',
                                         all_patches=('patchfoo',))
        with patch('iiqtools.iiqtools_patch.open', fake_open, create=True):
            result = iiqtools_patch.install_patch(patch_contents, patch_info, 'my_patch', fake_logger)
        expected = None

        self.assertEqual(result, expected)

    @patch.object(__builtin__, 'print')
    @patch.object(versions, 'get_patch_info')
    def test_handle_show_ok(self, fake_get_patch_info, fake_print):
        """iiqtools_patch.handle_show returns 0 (zero) upon success"""
        fake_logger = MagicMock()
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=False,
                                         readme='the readme contents',
                                         specific_patch='patch1234',
                                         all_patches=('patchfoo',))
        fake_get_patch_info.return_value = patch_info
        exit_code = iiqtools_patch.handle_show(specific_patch='', log=fake_logger)
        expected = 0

        self.assertEqual(exit_code, expected)

    @patch.object(__builtin__, 'print')
    @patch.object(versions, 'get_patch_info')
    def test_handle_show_details(self, fake_get_patch_info, fake_print):
        """iiqtools_patch.handle_show returns 0 (zero) upon success"""
        fake_logger = MagicMock()
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch1234',
                                         all_patches=('patch1234',))
        fake_get_patch_info.return_value = patch_info
        exit_code = iiqtools_patch.handle_show(specific_patch='patch1234', log=fake_logger)
        expected = 0

        self.assertEqual(exit_code, expected)

    @patch.object(__builtin__, 'print')
    @patch.object(versions, 'get_patch_info')
    def test_handle_show_not_installed(self, fake_get_patch_info, fake_print):
        """iiqtools_patch.handle_show returns 51 if the specific patch is not installed"""
        fake_logger = MagicMock()
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=False,
                                         readme='the readme contents',
                                         specific_patch='patch1234',
                                         all_patches=('patchfoo',))
        fake_get_patch_info.return_value = patch_info
        exit_code = iiqtools_patch.handle_show(specific_patch='patch1234', log=fake_logger)
        expected = 50

        self.assertEqual(exit_code, expected)

    @patch.object(__builtin__, 'print')
    @patch.object(versions, 'get_patch_info')
    def test_handle_show_no_readme(self, fake_get_patch_info, fake_print):
        """iiqtools_patch.handle_show returns 51 if the specific patch is not installed"""
        fake_logger = MagicMock()
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='',
                                         specific_patch='patch1234',
                                         all_patches=('patch1234',))
        fake_get_patch_info.return_value = patch_info
        exit_code = iiqtools_patch.handle_show(specific_patch='patch1234', log=fake_logger)
        expected = 51

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    @patch.object(iiqtools_patch, 'source_is_patchable')
    @patch.object(versions, 'get_patch_info')
    @patch.object(iiqtools_patch, 'install_patch')
    @patch.object(iiqtools_patch, 'extract_patch_contents')
    @patch.object(iiqtools_patch.os, 'mkdir')
    def test_handle_install(self, fake_mkdir, fake_extract_patch_contents,
        fake_install_patch, fake_get_patch_info, fake_source_is_patchable, fake_get_iiq_version):
        """iiqtools_patch.handle_install returns zero if patch is successfully installed"""
        fake_logger = MagicMock()
        fake_iiq_version = iiqtools_patch.versions.Version(name='insightiq', version='4.1.0.3')
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch9001',
                                         all_patches=('patch1234',))
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='[info]\nname=patch9001\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        fake_get_iiq_version.return_value = fake_iiq_version
        fake_extract_patch_contents.return_value = patch_contents
        fake_get_patch_info.return_value = patch_info

        exit_code = iiqtools_patch.handle_install(patch_path='my-patch.tgz', log=fake_logger)
        expected = 0

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    @patch.object(iiqtools_patch, 'source_is_patchable')
    @patch.object(versions, 'get_patch_info')
    @patch.object(iiqtools_patch, 'install_patch')
    @patch.object(iiqtools_patch, 'extract_patch_contents')
    @patch.object(iiqtools_patch.os, 'mkdir')
    def test_handle_install_no_iiq(self, fake_mkdir, fake_extract_patch_contents,
        fake_install_patch, fake_get_patch_info, fake_source_is_patchable, fake_get_iiq_version):
        """iiqtools_patch.handle_install returns 100 if InsightIQ is not installed"""
        fake_logger = MagicMock()
        fake_iiq_version = iiqtools_patch.versions.Version(name='insightiq', version='4.1.0.3')
        patch_info = versions.PatchInfo(iiq_dir='',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch9001',
                                         all_patches=('patch1234',))
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='[info]\nname=patch9001\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        fake_get_iiq_version.return_value = fake_iiq_version
        fake_extract_patch_contents.return_value = patch_contents
        fake_get_patch_info.return_value = patch_info

        exit_code = iiqtools_patch.handle_install(patch_path='my-patch.tgz', log=fake_logger)
        expected = 100

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    @patch.object(iiqtools_patch, 'source_is_patchable')
    @patch.object(versions, 'get_patch_info')
    @patch.object(iiqtools_patch, 'install_patch')
    @patch.object(iiqtools_patch, 'extract_patch_contents')
    @patch.object(iiqtools_patch.os, 'mkdir')
    def test_handle_install_permissions(self, fake_mkdir, fake_extract_patch_contents,
        fake_install_patch, fake_get_patch_info, fake_source_is_patchable, fake_get_iiq_version):
        """iiqtools_patch.handle_install returns 13 if it lacks permissions on the file system"""
        fake_logger = MagicMock()
        fake_iiq_version = iiqtools_patch.versions.Version(name='insightiq', version='4.1.0.3')
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch9001',
                                         all_patches=('patch1234',))
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='[info]\nname=patch9001\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        fake_get_iiq_version.return_value = fake_iiq_version
        fake_extract_patch_contents.return_value = patch_contents
        fake_get_patch_info.return_value = patch_info
        fake_mkdir.side_effect = IOError(13, 'permission denied', '/some/install/location')

        exit_code = iiqtools_patch.handle_install(patch_path='my-patch.tgz', log=fake_logger)
        expected = 13

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    @patch.object(iiqtools_patch, 'source_is_patchable')
    @patch.object(versions, 'get_patch_info')
    @patch.object(iiqtools_patch, 'install_patch')
    @patch.object(iiqtools_patch, 'extract_patch_contents')
    @patch.object(iiqtools_patch.os, 'mkdir')
    def test_handle_install_dir_exists(self, fake_mkdir, fake_extract_patch_contents,
        fake_install_patch, fake_get_patch_info, fake_source_is_patchable, fake_get_iiq_version):
        """iiqtools_patch.handle_install returns 0 even if the patches dir already exits"""
        fake_logger = MagicMock()
        fake_iiq_version = iiqtools_patch.versions.Version(name='insightiq', version='4.1.0.3')
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch9001',
                                         all_patches=('patch1234',))
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='[info]\nname=patch9001\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        fake_get_iiq_version.return_value = fake_iiq_version
        fake_extract_patch_contents.return_value = patch_contents
        fake_get_patch_info.return_value = patch_info
        fake_mkdir.side_effect = IOError(17, 'directory exists', '/some/install/location')

        exit_code = iiqtools_patch.handle_install(patch_path='my-patch.tgz', log=fake_logger)
        expected = 0

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    @patch.object(iiqtools_patch, 'source_is_patchable')
    @patch.object(versions, 'get_patch_info')
    @patch.object(iiqtools_patch, 'install_patch')
    @patch.object(iiqtools_patch, 'extract_patch_contents')
    @patch.object(iiqtools_patch.os, 'mkdir')
    def test_handle_install_mkdir_error(self, fake_mkdir, fake_extract_patch_contents,
        fake_install_patch, fake_get_patch_info, fake_source_is_patchable, fake_get_iiq_version):
        """iiqtools_patch.handle_install returns the IOError code if an unexpected error occurs"""
        fake_logger = MagicMock()
        fake_logger.level = 10
        fake_iiq_version = iiqtools_patch.versions.Version(name='insightiq', version='4.1.0.3')
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch9001',
                                         all_patches=('patch1234',))
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='[info]\nname=patch9001\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        fake_get_iiq_version.return_value = fake_iiq_version
        fake_extract_patch_contents.return_value = patch_contents
        fake_get_patch_info.return_value = patch_info
        fake_mkdir.side_effect = IOError(6, 'directory exists', '/some/install/location')

        exit_code = iiqtools_patch.handle_install(patch_path='my-patch.tgz', log=fake_logger)
        expected = 6

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    @patch.object(iiqtools_patch, 'source_is_patchable')
    @patch.object(versions, 'get_patch_info')
    @patch.object(iiqtools_patch, 'install_patch')
    @patch.object(iiqtools_patch, 'extract_patch_contents')
    @patch.object(iiqtools_patch.os, 'mkdir')
    def test_handle_install_bad_patch(self, fake_mkdir, fake_extract_patch_contents,
        fake_install_patch, fake_get_patch_info, fake_source_is_patchable, fake_get_iiq_version):
        """iiqtools_patch.handle_install returns 101 if patch file is malformed"""
        fake_logger = MagicMock()
        fake_iiq_version = iiqtools_patch.versions.Version(name='insightiq', version='4.1.0.3')
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch9001',
                                         all_patches=('patch1234',))
        patch_contents = iiqtools_patch.PatchContents(readme='', # no readme = bad patch
                                                 meta_ini='[info]\nname=patch9001\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        fake_get_iiq_version.return_value = fake_iiq_version
        fake_extract_patch_contents.return_value = patch_contents
        fake_get_patch_info.return_value = patch_info

        exit_code = iiqtools_patch.handle_install(patch_path='my-patch.tgz', log=fake_logger)
        expected = 101

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    @patch.object(iiqtools_patch, 'source_is_patchable')
    @patch.object(versions, 'get_patch_info')
    @patch.object(iiqtools_patch, 'install_patch')
    @patch.object(iiqtools_patch, 'extract_patch_contents')
    @patch.object(iiqtools_patch.os, 'mkdir')
    def test_handle_install_already_installed(self, fake_mkdir, fake_extract_patch_contents,
        fake_install_patch, fake_get_patch_info, fake_source_is_patchable, fake_get_iiq_version):
        """iiqtools_patch.handle_install returns 0 if patch already installed"""
        fake_logger = MagicMock()
        fake_iiq_version = iiqtools_patch.versions.Version(name='insightiq', version='4.1.0.3')
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch9001',
                                         all_patches=('patch1234',))
        patch_contents = iiqtools_patch.PatchContents(readme='the readme contents',
                                                 meta_ini='[info]\nname=patch1234\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        fake_get_iiq_version.return_value = fake_iiq_version
        fake_extract_patch_contents.return_value = patch_contents
        fake_get_patch_info.return_value = patch_info

        exit_code = iiqtools_patch.handle_install(patch_path='my-patch.tgz', log=fake_logger)
        expected = 0

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    @patch.object(iiqtools_patch, 'source_is_patchable')
    @patch.object(versions, 'get_patch_info')
    @patch.object(iiqtools_patch, 'install_patch')
    @patch.object(iiqtools_patch, 'extract_patch_contents')
    @patch.object(iiqtools_patch.os, 'mkdir')
    def test_handle_install_bad_version(self, fake_mkdir, fake_extract_patch_contents,
        fake_install_patch, fake_get_patch_info, fake_source_is_patchable, fake_get_iiq_version):
        """iiqtools_patch.handle_install returns 102 if patch doesn't apply to installed version of InsightIQ"""
        fake_logger = MagicMock()
        fake_iiq_version = iiqtools_patch.versions.Version(name='insightiq', version='3.1.0.3')
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch9001',
                                         all_patches=('patch1234',))
        patch_contents = iiqtools_patch.PatchContents(readme='the readme contents',
                                                 meta_ini='[info]\nname=patch9001\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        fake_get_iiq_version.return_value = fake_iiq_version
        fake_extract_patch_contents.return_value = patch_contents
        fake_get_patch_info.return_value = patch_info

        exit_code = iiqtools_patch.handle_install(patch_path='my-patch.tgz', log=fake_logger)
        expected = 102

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    @patch.object(iiqtools_patch, 'source_is_patchable')
    @patch.object(versions, 'get_patch_info')
    @patch.object(iiqtools_patch, 'install_patch')
    @patch.object(iiqtools_patch, 'extract_patch_contents')
    @patch.object(iiqtools_patch.os, 'mkdir')
    def test_handle_install_unpatchable(self, fake_mkdir, fake_extract_patch_contents,
        fake_install_patch, fake_get_patch_info, fake_source_is_patchable, fake_get_iiq_version):
        """iiqtools_patch.handle_install returns 103 if source fails patchable test"""
        fake_logger = MagicMock()
        fake_iiq_version = iiqtools_patch.versions.Version(name='insightiq', version='4.1.0.3')
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch9001',
                                         all_patches=('patch1234',))
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='[info]\nname=patch9001\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        fake_get_iiq_version.return_value = fake_iiq_version
        fake_extract_patch_contents.return_value = patch_contents
        fake_get_patch_info.return_value = patch_info
        fake_source_is_patchable.return_value = False

        exit_code = iiqtools_patch.handle_install(patch_path='my-patch.tgz', log=fake_logger)
        expected = 103

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch.versions, 'get_iiq_version')
    @patch.object(iiqtools_patch, 'source_is_patchable')
    @patch.object(versions, 'get_patch_info')
    @patch.object(iiqtools_patch, 'install_patch')
    @patch.object(iiqtools_patch, 'extract_patch_contents')
    @patch.object(iiqtools_patch.os, 'mkdir')
    def test_handle_install_ioerror(self, fake_mkdir, fake_extract_patch_contents,
        fake_install_patch, fake_get_patch_info, fake_source_is_patchable, fake_get_iiq_version):
        """iiqtools_patch.handle_install returns 104 if IOError occurs in the middle of installing"""
        fake_logger = MagicMock()
        fake_logger.level = 10
        fake_iiq_version = iiqtools_patch.versions.Version(name='insightiq', version='4.1.0.3')
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch9001',
                                         all_patches=('patch1234',))
        patch_contents = iiqtools_patch.PatchContents(readme='The readme contents',
                                                 meta_ini='[info]\nname=patch9001\nbug=1234\n[version]\nminimum=4.0\nmaximum=4.1.1\n[files]\nsome/file.py = themd5checksum',
                                                 patched_files={'some/file.py' : 'data'})
        fake_get_patch_info.return_value = patch_info
        fake_get_iiq_version.return_value = fake_iiq_version
        fake_extract_patch_contents.return_value = patch_contents
        fake_install_patch.side_effect = IOError(9, 'testerror', 'somefile')

        exit_code = iiqtools_patch.handle_install(patch_path='my-patch.tgz', log=fake_logger)
        expected = 104
        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch, 'restore_originals')
    @patch.object(iiqtools_patch, 'md5_matches')
    @patch.object(iiqtools_patch.shutil, 'rmtree')
    @patch.object(iiqtools_patch, 'expected_backups')
    @patch.object(iiqtools_patch.os, 'listdir')
    @patch.object(iiqtools_patch, 'ConfigObj')
    @patch.object(versions, 'get_patch_info')
    def test_handle_uninstall(self, fake_get_patch_info, fake_ConfigObj, fake_listdir,
        fake_expected_backups, fake_rmtree, fake_md5_matches, fake_restore_originals):
        """iiqtools_patch.handle_uninstall return zero when patch uninstall is successful"""
        fake_logger = MagicMock()
        fake_meta_config = MagicMock()
        fake_meta_config.__getitem__.return_value = {'insightiq/patched_file.py' : 'theMD5hash'}
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch1234',
                                         all_patches=('patch1234',))
        fake_get_patch_info.return_value = patch_info
        fake_ConfigObj.return_value = fake_meta_config

        exit_code = iiqtools_patch.handle_uninstall(patch_name='patch1234', log=fake_logger)
        expected = 0

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch, 'restore_originals')
    @patch.object(iiqtools_patch, 'md5_matches')
    @patch.object(iiqtools_patch.shutil, 'rmtree')
    @patch.object(iiqtools_patch, 'expected_backups')
    @patch.object(iiqtools_patch.os, 'listdir')
    @patch.object(iiqtools_patch, 'ConfigObj')
    @patch.object(versions, 'get_patch_info')
    def test_handle_uninstall_not_installed(self, fake_get_patch_info, fake_ConfigObj, fake_listdir,
        fake_expected_backups, fake_rmtree, fake_md5_matches, fake_restore_originals):
        """iiqtools_patch.handle_uninstall return 200 when patch isn't even installed"""
        fake_logger = MagicMock()
        fake_meta_config = MagicMock()
        fake_meta_config.__getitem__.return_value = {'insightiq/patched_file.py' : 'theMD5hash'}
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=False,
                                         readme='the readme contents',
                                         specific_patch='patch9001',
                                         all_patches=('patch1234',))
        fake_get_patch_info.return_value = patch_info
        fake_ConfigObj.return_value = fake_meta_config

        exit_code = iiqtools_patch.handle_uninstall(patch_name='patch1234', log=fake_logger)
        expected = 200

        self.assertEqual(exit_code, expected)


    @patch.object(iiqtools_patch, 'restore_originals')
    @patch.object(iiqtools_patch, 'md5_matches')
    @patch.object(iiqtools_patch.shutil, 'rmtree')
    @patch.object(iiqtools_patch, 'expected_backups')
    @patch.object(iiqtools_patch.os, 'listdir')
    @patch.object(iiqtools_patch, 'ConfigObj')
    @patch.object(versions, 'get_patch_info')
    def test_handle_uninstall_ioerror(self, fake_get_patch_info, fake_ConfigObj, fake_listdir,
        fake_expected_backups, fake_rmtree, fake_md5_matches, fake_restore_originals):
        """iiqtools_patch.handle_uninstall return 201 when patch uninstall encounters an IOError"""
        fake_logger = MagicMock()
        fake_ConfigObj.side_effect = IOError(9, 'some error', 'some file')
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch1234',
                                         all_patches=('patch1234',))
        fake_get_patch_info.return_value = patch_info

        exit_code = iiqtools_patch.handle_uninstall(patch_name='patch1234', log=fake_logger)
        expected = 201

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch, 'restore_originals')
    @patch.object(iiqtools_patch, 'md5_matches')
    @patch.object(iiqtools_patch.shutil, 'rmtree')
    @patch.object(iiqtools_patch, 'expected_backups')
    @patch.object(iiqtools_patch.os, 'listdir')
    @patch.object(iiqtools_patch, 'ConfigObj')
    @patch.object(versions, 'get_patch_info')
    def test_handle_uninstall_bad_backups(self, fake_get_patch_info, fake_ConfigObj, fake_listdir,
        fake_expected_backups, fake_rmtree, fake_md5_matches, fake_restore_originals):
        """iiqtools_patch.handle_uninstall return 202 when backup source files test fails"""
        fake_logger = MagicMock()
        fake_meta_config = MagicMock()
        fake_meta_config.__getitem__.return_value = {'insightiq/patched_file.py' : 'theMD5hash'}
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch1234',
                                         all_patches=('patch1234',))
        fake_get_patch_info.return_value = patch_info
        fake_expected_backups.return_value = False
        fake_ConfigObj.return_value = fake_meta_config

        exit_code = iiqtools_patch.handle_uninstall(patch_name='patch1234', log=fake_logger)
        expected = 202

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch, 'restore_originals')
    @patch.object(iiqtools_patch, 'md5_matches')
    @patch.object(iiqtools_patch.shutil, 'rmtree')
    @patch.object(iiqtools_patch, 'expected_backups')
    @patch.object(iiqtools_patch.os, 'listdir')
    @patch.object(iiqtools_patch, 'ConfigObj')
    @patch.object(versions, 'get_patch_info')
    def test_handle_uninstall_bad_md5(self, fake_get_patch_info, fake_ConfigObj, fake_listdir,
        fake_expected_backups, fake_rmtree, fake_md5_matches, fake_restore_originals):
        """iiqtools_patch.handle_uninstall return 203 when patch backup files have bad md5 values"""
        fake_logger = MagicMock()
        fake_meta_config = MagicMock()
        fake_meta_config.__getitem__.return_value = {'insightiq/patched_file.py' : 'theMD5hash'}
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch1234',
                                         all_patches=('patch1234',))
        fake_get_patch_info.return_value = patch_info
        fake_md5_matches.return_value = False
        fake_ConfigObj.return_value = fake_meta_config

        exit_code = iiqtools_patch.handle_uninstall(patch_name='patch1234', log=fake_logger)
        expected = 203

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch, 'restore_originals')
    @patch.object(iiqtools_patch, 'md5_matches')
    @patch.object(iiqtools_patch.shutil, 'rmtree')
    @patch.object(iiqtools_patch, 'expected_backups')
    @patch.object(iiqtools_patch.os, 'listdir')
    @patch.object(iiqtools_patch, 'ConfigObj')
    @patch.object(versions, 'get_patch_info')
    def test_handle_uninstall_ioerror_restore(self, fake_get_patch_info, fake_ConfigObj, fake_listdir,
        fake_expected_backups, fake_rmtree, fake_md5_matches, fake_restore_originals):
        """iiqtools_patch.handle_uninstall return the errno of the IOError if one is encountered while restoring originals"""
        fake_logger = MagicMock()
        fake_meta_config = MagicMock()
        fake_meta_config.__getitem__.return_value = {'insightiq/patched_file.py' : 'theMD5hash'}
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch1234',
                                         all_patches=('patch1234',))
        fake_get_patch_info.return_value = patch_info
        fake_ConfigObj.return_value = fake_meta_config
        fake_restore_originals.side_effect = IOError(90, 'some error', 'some file')


        exit_code = iiqtools_patch.handle_uninstall(patch_name='patch1234', log=fake_logger)
        expected = 90

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch, 'restore_originals')
    @patch.object(iiqtools_patch, 'md5_matches')
    @patch.object(iiqtools_patch.shutil, 'rmtree')
    @patch.object(iiqtools_patch, 'expected_backups')
    @patch.object(iiqtools_patch.os, 'listdir')
    @patch.object(iiqtools_patch, 'ConfigObj')
    @patch.object(versions, 'get_patch_info')
    def test_handle_uninstall_rm_failure(self, fake_get_patch_info, fake_ConfigObj, fake_listdir,
        fake_expected_backups, fake_rmtree, fake_md5_matches, fake_restore_originals):
        """iiqtools_patch.handle_uninstall return the errno encounted if it fails to remove the patch reference"""
        fake_logger = MagicMock()
        fake_meta_config = MagicMock()
        fake_meta_config.__getitem__.return_value = {'insightiq/patched_file.py' : 'theMD5hash'}
        patch_info = versions.PatchInfo(iiq_dir='some/dir',
                                         patches_dir='some/dir/patches',
                                         is_installed=True,
                                         readme='the readme contents',
                                         specific_patch='patch1234',
                                         all_patches=('patch1234',))
        fake_get_patch_info.return_value = patch_info
        fake_ConfigObj.return_value = fake_meta_config
        fake_rmtree.side_effect = IOError(95, 'some error', 'some file')


        exit_code = iiqtools_patch.handle_uninstall(patch_name='patch1234', log=fake_logger)
        expected = 95

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch.shell, 'run_cmd')
    @patch.object(iiqtools_patch, 'handle_uninstall')
    @patch.object(iiqtools_patch, 'handle_install')
    @patch.object(iiqtools_patch, 'handle_show')
    @patch.object(iiqtools_patch, 'get_logger')
    def test_main_show_ok(self, fake_get_logger, fake_handle_show, fake_handle_install,
    fake_handle_uninstall, fake_run_cmd):
        """iiqtools_patch.main --show returns zero upon success"""
        fake_handle_show.return_value = 0
        fake_handle_install.return_value = 0
        fake_handle_uninstall.return_value = 0
        fake_get_logger.return_value = MagicMock()

        exit_code = iiqtools_patch.main(['--show'])
        expected = 0

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch, 'check_file')
    @patch.object(iiqtools_patch.shell, 'run_cmd')
    @patch.object(iiqtools_patch, 'handle_uninstall')
    @patch.object(iiqtools_patch, 'handle_install')
    @patch.object(iiqtools_patch, 'handle_show')
    @patch.object(iiqtools_patch, 'get_logger')
    def test_main_install_ok(self, fake_get_logger, fake_handle_show, fake_handle_install,
    fake_handle_uninstall, fake_run_cmd, fake_check_file):
        """iiqtools_patch.main --install returns zero upon success"""
        fake_handle_show.return_value = 0
        fake_handle_install.return_value = 0
        fake_handle_uninstall.return_value = 0
        fake_get_logger.return_value = MagicMock()
        fake_check_file.return_value = 'mypatch.tgz'

        exit_code = iiqtools_patch.main(['--install', 'mypatch.tgz'])
        expected = 0

        self.assertEqual(exit_code, expected)

    @patch.object(iiqtools_patch.shell, 'run_cmd')
    @patch.object(iiqtools_patch, 'handle_uninstall')
    @patch.object(iiqtools_patch, 'handle_install')
    @patch.object(iiqtools_patch, 'handle_show')
    @patch.object(iiqtools_patch, 'get_logger')
    def test_main_uninstall_ok(self, fake_get_logger, fake_handle_show, fake_handle_install,
    fake_handle_uninstall, fake_run_cmd):
        """iiqtools_patch.main --install returns zero upon success"""
        fake_handle_show.return_value = 0
        fake_handle_install.return_value = 0
        fake_handle_uninstall.return_value = 0
        fake_get_logger.return_value = MagicMock()

        exit_code = iiqtools_patch.main(['--uninstall', 'mypatch.tgz'])
        expected = 0

        self.assertEqual(exit_code, expected)


if __name__ == '__main__':
    unittest.main()
