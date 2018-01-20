# -*- coding: UTF-8 -*-
"""
Unit tests for the Version object
"""
import unittest
from mock import patch, MagicMock

from iiqtools.utils import versions


class TestInit(unittest.TestCase):
    """A suite of tests for non-comparison operator specific functionality"""

    def test_init_ok(self):
        """Able to instantiate the Version object"""
        v1 = versions.Version(version='1.2.3', name='foo')
        self.assertTrue(isinstance(v1, versions.Version))

    def test_invalid_version_ints(self):
        """Version only support integer version values"""
        self.assertRaises(ValueError, versions.Version, version='1a.2', name='foo')

    def test_invalid_version_fields(self):
        """Version requires at least Major.Minor for verisons"""
        self.assertRaises(ValueError, versions.Version, version='1234', name='foo')

    def test_invalid_version_value(self):
        """Version only accepts strings for version param"""
        self.assertRaises(TypeError, versions.Version, version=1, name='foo')

    def test_name_property_ro(self):
        """Version.name is read only"""
        v1 = versions.Version(version='1.2.3', name='foo')
        try:
            v1.name = 'bar'
        except AttributeError:
            passed = True
        else:
            passed = False

        self.assertTrue(passed)

    def test_semver_property_ro(self):
        """Version.semver is read only"""
        v1 = versions.Version(version='1.2.3', name='foo')
        try:
            v1.semver = 'bar'
        except AttributeError:
            passed = True
        else:
            passed = False

        self.assertTrue(passed)

    def test_version_property_ro(self):
        """Version.version is read only"""
        v1 = versions.Version(version='1.2.3', name='foo')
        try:
            v1.version = '3.4'
        except AttributeError:
            passed = True
        else:
            passed = False

        self.assertTrue(passed)

    def test_major_property_ro(self):
        """Version.major is read only"""
        v1 = versions.Version(version='1.2.3', name='foo')
        try:
            v1.major = 12
        except AttributeError:
            passed = True
        else:
            passed = False

        self.assertTrue(passed)

    def test_minor_property_ro(self):
        """Version.minor is read only"""
        v1 = versions.Version(version='1.2.3', name='foo')
        try:
            v1.minor = 33
        except AttributeError:
            passed = True
        else:
            passed = False

        self.assertTrue(passed)

    def test_patch_property_ro(self):
        """Version.patch is read only"""
        v1 = versions.Version(version='1.2.3', name='foo')
        try:
            v1.patch = 234
        except AttributeError:
            passed = True
        else:
            passed = False

        self.assertTrue(passed)

    def test_build_property_ro(self):
        """Version.build is read only"""
        v1 = versions.Version(version='1.2.3', name='foo')
        try:
            v1.build = 9001
        except AttributeError:
            passed = True
        else:
            passed = False

        self.assertTrue(passed)

    def test_name_property(self):
        """Version.name is the expected value"""
        v1 = versions.Version(version='1.2.3', name='foo')
        expected = 'foo'

        self.assertEqual(v1.name, expected)

    def test_semver_property(self):
        """Version.semver is read only"""
        v1 = versions.Version(version='1.2.3', name='foo')
        expected = ('major', 'minor', 'patch', 'build')

        self.assertEqual(v1.semver, expected)

    def test_version_property(self):
        """Version.version is read only"""
        v1 = versions.Version(version='1.2.3', name='foo')
        expected = '1.2.3'

        self.assertEqual(v1.version, expected)

    def test_major_property(self):
        """Version.major is read only"""
        v1 = versions.Version(version='1.2.3', name='foo')
        expected = 1

        self.assertEqual(v1.major, expected)

    def test_minor_property(self):
        """Version.minor is read only"""
        v1 = versions.Version(version='1.2.3', name='foo')
        expected = 2

        self.assertEqual(v1.minor, expected)

    def test_patch_property(self):
        """Version.patch is read only"""
        v1 = versions.Version(version='1.2.3', name='foo')
        expected = 3

        self.assertEqual(v1.patch, expected)

    def test_build_property(self):
        """Version.build is read only"""
        v1 = versions.Version(version='1.2.3.4', name='foo')
        expected = 4

        self.assertEqual(v1.build, expected)

    def test_undefined_semver(self):
        """Version - properties that are undefined are ``None``"""
        v1 = versions.Version(version='1.2.3', name='foo')
        expected = None

        self.assertEqual(v1.build, expected)

    def test_hash(self):
        """Version objects are hashable, i.e. can be added to a dictionary"""
        v1 = versions.Version(version='1.2.3', name='foo')
        my_dict = { v1 : 'foo'}

        self.assertTrue(isinstance(my_dict, dict))

    def test_get_other_typeerror(self):
        """Version._get_other supports only strings or Version as param"""
        v = versions.Version(name='foo', version='1.2.3')
        self.assertRaises(TypeError, v._get_other, 3.4)

    def test_get_other_typeerror_2(self):
        """Version._get_other - Invalid version strings raises a TypeError"""
        v = versions.Version(name='foo', version='1.2.3')
        self.assertRaises(TypeError, v._get_other, '1')


class TestEquals(unittest.TestCase):
    """A suite of tests that compare equality, ``==``"""

    def test_a(self):
        """Version - identical versions values are equal, regardless of name"""
        v1 = versions.Version(version='1.2.3', name='foo')
        v2 = versions.Version(version='1.2.3', name='bar')

        self.assertTrue(v1 == v2)
        self.assertTrue(v2 == v1)

    def test_b(self):
        """Version - versions that are longer are not equal, regardless of name"""
        v1 = versions.Version(version='1.2.3', name='foo')
        v2 = versions.Version(version='1.2', name='bar')

        self.assertFalse(v1 == v2)
        self.assertFalse(v2 == v1)

    def test_c(self):
        """Version - different versions are not equal, regardless of name"""
        v1 = versions.Version(version='1.2.3', name='foo')
        v2 = versions.Version(version='2.2.3', name='bar')

        self.assertFalse(v1 == v2)
        self.assertFalse(v2 == v1)

    def test_d(self):
        """Version - the equals operator works with strings"""
        v1 = versions.Version(version='1.2.3', name='foo')

        self.assertTrue(v1 == '1.2.3')


class TestNotEquals(unittest.TestCase):
    """A suite of test that compare not equivalence, ``!=``"""

    def test_a(self):
        """Version - different versions are not equal, regardless of name"""
        v1 = versions.Version(version='1.2.3', name='foo')
        v2 = versions.Version(version='2.2.3', name='bar')

        self.assertTrue(v1 != v2)
        self.assertTrue(v2 != v1)

    def test_b(self):
        """Version - versions that are of different lengths are not equal, regardless of name"""
        v1 = versions.Version(version='1.2.3', name='foo')
        v2 = versions.Version(version='1.2', name='bar')

        self.assertTrue(v1 != v2)
        self.assertTrue(v2 != v1)


    def test_c(self):
        """Version - the same versions are not not-equal, regardless of name"""
        v1 = versions.Version(version='1.2.3', name='foo')
        v2 = versions.Version(version='1.2.3', name='bar')

        self.assertFalse(v1 != v2)
        self.assertFalse(v2 != v1)

    def test_d(self):
        """Version the not equals operator works with strings"""
        v1 = versions.Version(version='1.2.3', name='foo')

        self.assertTrue(v1 != '3.4')


class TestLessThan(unittest.TestCase):
    """A suite of test that compare less than, ``<``"""

    def test_a(self):
        """Version - equal versions are not less than"""
        v1 = versions.Version(version='1.2.3', name='foo')
        v2 = versions.Version(version='1.2.3', name='bar')

        self.assertFalse(v1 < v2)
        self.assertFalse(v2 < v1)

    def test_b(self):
        """Version - Less specific versions that are otherwise identical are less than"""
        v1 = versions.Version(version='1.2.3', name='foo')
        v2 = versions.Version(version='1.2', name='bar')

        self.assertFalse(v1 < v2)
        self.assertTrue(v2 < v1)

    def test_c(self):
        """Version - ``None`` is less than zero"""
        v1 = versions.Version(version='1.2.0', name='foo')
        v2 = versions.Version(version='1.2', name='bar')

        self.assertFalse(v1 < v2)
        self.assertTrue(v2 < v1)

    def test_d(self):
        """Version - Larger versions are not less than"""
        v1 = versions.Version(version='1.2.1', name='foo')
        v2 = versions.Version(version='1.2.2', name='bar')

        self.assertTrue(v1 < v2)
        self.assertFalse(v2 < v1)

    def test_e(self):
        """Version - The less than operator works with strings"""
        v1 = versions.Version(version='1.2.1', name='foo')

        self.assertTrue(v1 < '3.4.5.6')


class TestGreaterThan(unittest.TestCase):
    """A suite of test that compare less than, ``>``"""

    def test_a(self):
        """Version - equal versions are not greater than"""
        v1 = versions.Version(version='1.2.3', name='foo')
        v2 = versions.Version(version='1.2.3', name='bar')

        self.assertFalse(v1 > v2)
        self.assertFalse(v2 > v1)

    def test_b(self):
        """Version - Less specific versions that are otherwise identical are less than"""
        v1 = versions.Version(version='1.2.3', name='foo')
        v2 = versions.Version(version='1.2', name='bar')

        self.assertFalse(v1 < v2)
        self.assertTrue(v2 < v1)

    def test_c(self):
        """Version - zero is greater than ``None``"""
        v1 = versions.Version(version='1.2.0', name='foo')
        v2 = versions.Version(version='1.2', name='bar')

        self.assertTrue(v1 > v2)
        self.assertFalse(v2 > v1)

    def test_d(self):
        """Version - Larger versions are greater than"""
        v1 = versions.Version(version='1.2.1', name='foo')
        v2 = versions.Version(version='1.2.2', name='bar')

        self.assertFalse(v1 > v2)
        self.assertTrue(v2 > v1)

    def test_e(self):
        """Version - The greater than operator works with strings"""
        v1 = versions.Version(version='3.2.1', name='foo')

        self.assertTrue(v1 > '2.3')


class TestLessThanEqualTo(unittest.TestCase):
    """A suite of test that compare less than, ``<=``"""

    def test_a(self):
        """Version - Larger version are not less than or equal to"""
        v1 = versions.Version(version='1.2.1', name='foo')
        v2 = versions.Version(version='1.2.2', name='bar')

        self.assertTrue(v1 <= v2)
        self.assertFalse(v2 <= v1)

    def test_b(self):
        """Version - Equal versions are less than or equal to"""
        v1 = versions.Version(version='1.2.1', name='foo')
        v2 = versions.Version(version='1.2.1', name='bar')

        self.assertTrue(v1 <= v2)
        self.assertTrue(v2 <= v1)

    def test_c(self):
        """Version - Less specific versions are less than or equal"""
        v1 = versions.Version(version='1.2', name='foo')
        v2 = versions.Version(version='1.2.1', name='bar')

        self.assertTrue(v1 <= v2)
        self.assertFalse(v2 <= v1)

    def test_d(self):
        """Version - The less than or equal to operator works with strings"""
        v1 = versions.Version(version='1.2', name='foo')

        self.assertTrue(v1 <= '1.2')


class TestGreaterThanEqualTo(unittest.TestCase):
    """A suite of test that compare less than, ``>=``"""

    def test_a(self):
        """Version - Larger version are not less than or equal to"""
        v1 = versions.Version(version='1.2.1', name='foo')
        v2 = versions.Version(version='1.2.2', name='bar')

        self.assertFalse(v1 >= v2)
        self.assertTrue(v2 >= v1)

    def test_b(self):
        """Version - Equal versions are less than or equal to"""
        v1 = versions.Version(version='1.2.1', name='foo')
        v2 = versions.Version(version='1.2.1', name='bar')

        self.assertTrue(v1 >= v2)
        self.assertTrue(v2 >= v1)

    def test_c(self):
        """Version - Less specific versions are less than or equal"""
        v1 = versions.Version(version='1.2', name='foo')
        v2 = versions.Version(version='1.2.1', name='bar')

        self.assertFalse(v1 >= v2)
        self.assertTrue(v2 >= v1)

    def test_d(self):
        """Version - Greather than or equal to operator supports strings"""
        v1 = versions.Version(version='1.2', name='foo')

        self.assertTrue(v1 >= '1.0')


class TestGetVersions(unittest.TestCase):
    """A suite of tests for the ``get_iiq_version`` and ``get_iiqtools_version`` functions"""

    class FakeDistVersion(object):
        """For replacing what ``get_distribution`` returns in testing"""
        def __init__(self, version):
            self.version = version

    @patch.object(versions, 'get_distribution')
    def test_get_iiq_version(self, fake_get_distribution):
        """None is returned if InsightIQ is not installed"""
        fake_get_distribution.side_effect = [versions.DistributionNotFound()]

        v = versions.get_iiq_version()

        self.assertTrue(v is None)

    @patch.object(versions, 'get_distribution')
    def test_get_iiqtools_version(self, fake_get_distribution):
        """None is returned if IIQTools is not installed"""
        fake_get_distribution.side_effect = [versions.DistributionNotFound()]

        v = versions.get_iiqtools_version()

        self.assertTrue(v is None)

    @patch.object(versions, 'get_distribution')
    def test_get_iiq_version_ok(self, fake_get_distribution):
        """Version is returned if InsightIQ is  installed"""
        fake_get_distribution.return_value = self.FakeDistVersion('3.3.4')

        v = versions.get_iiq_version()

        self.assertTrue(isinstance(v, versions.Version))

    @patch.object(versions, 'get_distribution')
    def test_get_iiqtools_version_ok(self, fake_get_distribution):
        """Version is returned if IIQTools is installed"""
        fake_get_distribution.return_value = self.FakeDistVersion('1.2.3')

        v = versions.get_iiqtools_version()

        self.assertTrue(isinstance(v, versions.Version))

class TestPatchInfo(unittest.TestCase):
    """TODO"""

    def test_patch_info(self):
        """The PatchInfo API accepts the expected params"""
        patch_info = versions.PatchInfo(iiq_dir='/some/path',
                                         patches_dir='/another/path',
                                         is_installed=False,
                                         specific_patch='this_patch',
                                         readme='data from readme',
                                         all_patches=('patch1', 'patch2'))
        self.assertTrue(isinstance(patch_info, versions._PatchInfo))

    def test_get_patch_info_returns(self):
        """versions.get_patch_info always returns a PatchInfo object"""
        # This test assumes IIQ isn't installed, thus the pile of errors that'll
        # occur shouldn't prevent us from getting a PatchInfo object
        fake_log = MagicMock()
        patch_info = versions.get_patch_info('bogus-patch.tgz', fake_log)

        self.assertTrue(isinstance(patch_info, versions._PatchInfo))
        self.assertEqual(patch_info.iiq_dir, '')
















if __name__ == '__main__':
    unittest.main()
