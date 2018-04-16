# -*- UTF-8 -*-
"""
Unit tests for the iiqtools.utils.insightiq_api module
"""
import unittest
import collections
from mock import patch, MagicMock

import requests

from iiqtools.utils import insightiq_api


class TestInsightiqApi(unittest.TestCase):
    """A suite of test cases for the InsightiqApi object"""

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.patcher = patch.object(insightiq_api.InsightiqApi, '_get_session')
        cls.fake_renew_session = cls.patcher.start()
        cls.fake_session = MagicMock()
        cls.fake_renew_session.return_value = cls.fake_session

    @classmethod
    def tearDown(cls):
        """Runs after every test case"""
        cls.patcher.stop()
        cls.fake_renew_session = None

    def test_init(self):
        """InsightiqApi - Automatically sets up the HTTP session with InsightIQ"""
        iiq = insightiq_api.InsightiqApi(username='pat', password='a')

        self.fake_renew_session.assert_called()

    def test_end_session(self):
        """InsightiqApi - ``.end_session()`` closes the TCP socket and logs out of the IIQ session"""
        iiq = insightiq_api.InsightiqApi(username='pat', password='a')
        iiq.end_session()

        self.fake_session.get.assert_called()
        self.fake_session.close.assert_called()

    def test_build_uri(self):
        """InsightiqApi - ``_build_uri()`` works with no slashes in the endpoint"""
        iiq = insightiq_api.InsightiqApi(username='pat', password='a')

        value = iiq._build_uri('someEndpoint')
        expected = 'https://localhost/someEndpoint'

        self.assertEqual(value, expected)

    def test_build_uri_slashs(self):
        """InsightiqApi - ``_build_uri()`` works with slashes in the endpoint"""
        iiq = insightiq_api.InsightiqApi(username='pat', password='a')

        value = iiq._build_uri('/someEndpoint')
        expected = 'https://localhost/someEndpoint'

        self.assertEqual(value, expected)

    def test_username(self):
        """InsightiqApi - The supplied username can be read"""
        iiq = insightiq_api.InsightiqApi(username='pat', password='a')

        value = iiq.username
        expected = 'pat'

        self.assertEqual(value, expected)

    def test_username_readonly(self):
        """InsightiqApi - The username is readonly"""
        iiq = insightiq_api.InsightiqApi(username='pat', password='a')

        with self.assertRaises(AttributeError):
            iiq.username = 'bob'

    def test_with_statement(self):
        """InsightiqApi - using in a ``with`` statement auto-handles the session"""
        with insightiq_api.InsightiqApi(username='pat', password='a') as iiq:
            pass

        self.fake_session.close.assert_called()
        self.fake_session.get.assert_called()

    def test_call(self):
        """InsightiqApi - ``_call()`` pulls the HTTP method from the session object"""
        iiq = insightiq_api.InsightiqApi(username='pat', password='a')
        _ = iiq._call('someEndpoint', method='head')

        self.fake_session.head.assert_called()


class TestInsightiqApiRenewSession(unittest.TestCase):
    """A suite of tests for the ``renew_session()`` method"""

    @classmethod
    def setUp(cls):
        """Runs before every test case"""
        cls.patcher = patch.object(insightiq_api, 'requests')
        cls.fake_requests = cls.patcher.start()
        cls.fake_session = MagicMock()
        cls.fake_requests.Session.return_value = cls.fake_session

    @classmethod
    def tearDown(cls):
        """Runs after every test case"""
        cls.patcher.stop()
        cls.fake_requests = None

    def test_session(self):
        """InsightiqApi - ``renew_session()`` returns a requests.Session"""
        iiq = insightiq_api.InsightiqApi(username='pat', password='a')

        self.assertTrue(iiq._session is self.fake_session)

    def test_session_post(self):
        """InsightiqApi - ``renew_session()`` post to create IIQ session"""
        iiq = insightiq_api.InsightiqApi(username='pat', password='a')

        args, kwargs = self.fake_session.post.call_args
        expected_url = 'https://localhost/login'
        expected_data = {'username': 'pat', 'authform': '+Log+in+', 'password': 'a'}

        self.assertEqual(args[0], expected_url)
        self.assertEqual(kwargs['data'], expected_data)

    def test_status(self):
        """InsightiqApi - ``renew_session()`` checks the HTTP status code"""
        fake_post = MagicMock()
        self.fake_session.post.return_value = fake_post
        iiq = insightiq_api.InsightiqApi(username='pat', password='a')

        fake_post.raise_for_status.assert_called()


class TestInsightiqSessions(unittest.TestCase):
    """A suite of tests for the session creation logic in InsightiqApi"""

    @patch.object(insightiq_api.InsightiqApi, '_get_session')
    def test_session_retries(self, fake_get_session):
        """InsightiqApi - ``renew_session()`` will try 3 times to get a valid session"""
        fake_get_session.side_effect = [requests.exceptions.ConnectionError('testing'),
                                        requests.exceptions.ConnectionError('testing'),
                                        requests.exceptions.ConnectionError('testing'),
                                        requests.exceptions.ConnectionError('testing'),]

        try:
            insightiq_api.InsightiqApi(username='bob', password='a')
        except Exception as doh:
            # this will raise connection error, but we're not testing that here
            pass

        call_count = fake_get_session.call_count
        expected = 3

        self.assertEqual(call_count, expected)

    @patch.object(insightiq_api.InsightiqApi, '_get_session')
    def test_connection_error(self, fake_get_session):
        """InsightiqApi - failure to obtain a session raises ConnectionError"""
        fake_get_session.side_effect = [requests.exceptions.ConnectionError('testing'),
                                        requests.exceptions.ConnectionError('testing'),
                                        requests.exceptions.ConnectionError('testing'),
                                        requests.exceptions.ConnectionError('testing'),]

        with self.assertRaises(insightiq_api.ConnectionError):
                insightiq_api.InsightiqApi(username='bob', password='a')


class TestParametersInit(unittest.TestCase):
    """A suite of test cases for init options of the Parameters object"""

    def test_init_odict(self):
        """Parameters can be instantiated with a `collections.OrderedDict`"""
        odict = collections.OrderedDict(one=1)
        params = insightiq_api.Parameters(odict)

        expected = [['one', 1]]
        actual = params._data

        self.assertEqual(expected, actual)

    def test_init_keywords(self):
        """Parameters can be instantiated with keyword arguments"""
        params = insightiq_api.Parameters(one=1)

        expected = [['one', 1]]
        actual = params._data

        self.assertEqual(expected, actual)

    def test_init_dict(self):
        """Parameters can be instantiated with a normal dictionary"""
        params = insightiq_api.Parameters({'one' : 1})

        expected = [['one', 1]]
        actual = params._data

        self.assertEqual(expected, actual)

    def test_init_params(self):
        """Parameters can be instantiated with another instance of Parameters"""
        params_1 = insightiq_api.Parameters({'one' : 1})
        params = insightiq_api.Parameters(params_1)

        expected = [['one', 1]]
        actual = params._data

        self.assertEqual(expected, actual)

    def test_init_params_list(self):
        """Parameters can be instantiated with a list of key/value pairs"""
        params = insightiq_api.Parameters([('one', 1), ('two', 2)])

        value = params._data
        expected = [['one', 1], ['two', 2]]

        self.assertEqual(value, expected)

    def test_init_params_list_bad(self):
        """Parameters cannot be instantiated with a random list"""
        with self.assertRaises(ValueError):
            insightiq_api.Parameters(['one', 1, 'two', 2])

    def test_init_params_complex_list(self):
        """Parameters supports list of multiple valid types"""
        params = insightiq_api.Parameters([{'one' : 1}, ('two', 2)])

        value = params._data
        expected = [['one', 1], ['two', 2]]

        self.assertEqual(value, expected)

    def test_init_params_tuple_too_long(self):
        """Parameters wont accept a tuple/list when it's length  is not two"""
        with self.assertRaises(ValueError):
            insightiq_api.Parameters([(2,3,4,5)])


class TestParametersDictApi(unittest.TestCase):
    """A suite of test cases to ensure the Parameters object supports the standard Dictionary API"""

    def test_getitem(self):
        """Parameters supports dictionary syntax for retrieving an attribute"""
        params = insightiq_api.Parameters(one=1)
        try:
            value = params['one']
        except TypeError as doh:
            value = '%s' % doh

        self.assertEqual(value, 1)

    def test_getitem_keyerror(self):
        """Parameters - asking for a non-existant parameter raises KeyError"""
        params = insightiq_api.Parameters()
        with self.assertRaises(KeyError):
            params['doh']

    def test_setattr(self):
        """Parameters support dictionary syntax for setting an attribute"""
        params = insightiq_api.Parameters()
        try:
            params['one'] = 1
        except TypeError as doh:
            value = '%s' % doh
        else:
            value = params._data
        expected = [['one', 1]]

        self.assertEqual(value, expected)

    def test_setattr_modifies(self):
        """Parameters supports changing param values via the dictionary syntax"""
        params = insightiq_api.Parameters(one=1)
        params['one'] = 2

        value = params.get('one')
        expected = 2

        self.assertEqual(value, expected)

    def test_delitem_no_param(self):
        """Parameters raises KeyError when trying to delete a param that doesn't exist"""
        params = insightiq_api.Parameters()
        with self.assertRaises(KeyError):
            del params['foo']

    def test_items(self):
        """Parameters supports the `.items()` method"""
        params = insightiq_api.Parameters({'one': 1}, {'one': 'foo'})
        value = list(params.items()) # using list() b/c newer versions of Python return a generator
        expected = [('one', 1), ('one', 'foo')]

        self.assertEqual(value, expected)

    def test_keys(self):
        """Parameters supports the `.keys()` method"""
        params = insightiq_api.Parameters(one=1)
        value = list(params.keys())
        expected = ['one']

        self.assertEqual(value, expected)

    def test_pop(self):
        """Parameters support the `.pop()` method"""
        params = insightiq_api.Parameters(one=1)
        value = params.pop('one')
        expected = 1

        self.assertEqual(value, expected)

    def test_len(self):
        """Parameters returns the correct answer for ``len()``"""
        params = insightiq_api.Parameters({'one' : 'foo'}, one=1, two=2)
        value = len(params)
        expected = 3

        self.assertEqual(value, expected)


class TestParametersExtendedApi(unittest.TestCase):
    """A suite of test cases for the additional functionality that extends the Dictionary API"""

    def test_NAME(self):
        """Parameters - the NAME property is 0"""
        params = insightiq_api.Parameters()

        value = params.NAME
        expected = 0

        self.assertEqual(value, expected)

    def test_NAME_readonly(self):
        """Parameters - the NAME property is read only"""
        params = insightiq_api.Parameters()
        with self.assertRaises(AttributeError):
            params.NAME = 'foo'

    def test_VALUE(self):
        """Parameters - the VALUE property is 1"""
        params = insightiq_api.Parameters()

        value = params.VALUE
        expected = 1

        self.assertEqual(value, expected)

    def test_VALUE_readonly(self):
        """Parameters - the VALUE property is read only"""
        params = insightiq_api.Parameters()
        with self.assertRaises(AttributeError):
            params.VALUE = 'foo'

    def test_get_all(self):
        """Parameters - ``.get_all()`` returns all instances of duplicate parameters"""
        params = insightiq_api.Parameters({'one': 1}, {'one': 'foo'}, {'two': 'bar'})
        value = params.get_all('one')
        expected = [['one', 1], ['one', 'foo']]

        self.assertEqual(value, expected)

    def test_add(self):
        """Parameters - ``add()`` creats duplicate entries for the same parameter name"""
        params = insightiq_api.Parameters(one=1)
        params.add(name='one', value='foo')

        value = params._data
        expected = [['one', 1], ['one', 'foo']]

        self.assertEqual(value, expected)

    def test_delete_parameter(self):
        """Parameters can delete a specific instance of a parameter"""
        params = insightiq_api.Parameters({'one': 1}, {'one': 2}, {'one': 3})
        # order of the init args == order of the occurrence
        params.delete_parameter(name='one', occurrence=1) # base zero, so the 2nd

        value = params.get_all('one')
        expected = [['one', 1], ['one', 3]]

        self.assertEqual(value, expected)

    def test_delete_parameter_no_exist(self):
        """Parameters raises KeyError when trying to delete a parameter does not exist"""
        params = insightiq_api.Parameters(one=1)
        with self.assertRaises(KeyError):
            params.delete_parameter(name='foo', occurrence=1)

    def test_delete_parameter_no_occurrence(self):
        """Parameters raises KeyError when trying to delete an occurrence that does not exist"""
        params = insightiq_api.Parameters(one=1)
        with self.assertRaises(KeyError):
            params.delete_parameter(name='one', occurrence=200)

    def test_modify_parameter(self):
        """Parameters can change a specific instance of parameters"""
        params = insightiq_api.Parameters({'one': 1}, {'one': 3})
        params.modify_parameter(name='one', new_value=2, occurrence=1)

        value = params.get_all('one')
        expected = [['one', 1], ['one', 2]]

        self.assertEqual(value, expected)

    def test_modify_parameter_no_exist(self):
        """Parameters raises KeyError when trying to modify a parameter does not exist"""
        params = insightiq_api.Parameters(one=1)
        with self.assertRaises(KeyError):
            params.modify_parameter(name='foo', new_value=2, occurrence=1)

    def test_modify_parameter_no_occurrence(self):
        """Parameters raises KeyError when trying to modify an occurrence that does not exist"""
        params = insightiq_api.Parameters(one=1)
        with self.assertRaises(KeyError):
            params.modify_parameter(name='one', new_value=2, occurrence=200)


class TestParametersUseCases(unittest.TestCase):
    """A suite of tests for how users work with and manipulate Parameters"""

    def test_building_query_string(self):
        """Parameters - iterating the object to build an HTTP query string is simple"""
        params = insightiq_api.Parameters({'one': 1}, {'one': 'foo'}, {'two': 'bar'})
        tmp = []
        for param, value in params.items():
            tmp.append('%s=%s' % (param, value))
        query = '&'.join(tmp)
        expected = 'one=1&one=foo&two=bar'

        self.assertEqual(query, expected)

    def test_iterative_addition(self):
        """Parameters - adding duplicate params works in a for-loop"""
        params = insightiq_api.Parameters()
        for value in range(3):
            params.add('guid', value)

        value = params.get_all('guid')
        expected = [['guid', 0], ['guid', 1], ['guid', 2]]

        self.assertEqual(value, expected)

    def test_modify_occurrence(self):
        """Parameters - changing the value of a specific param works"""
        params = insightiq_api.Parameters({'one': 1}, {'one': 'foo'}, {'two': 2})
        ones = params.get_all('one')
        for index, pair in enumerate(ones):
            if pair[params.VALUE] == 'foo':
                # deleting a specific param would just call the ``.delete_parameter()`` method instead
                params.modify_parameter(name=pair[params.NAME], new_value='bar', occurrence=index)

        value = params._data
        expected = [['one', 1], ['one', 'bar'], ['two', 2]]

        self.assertEqual(value, expected)


if __name__ == '__main__':
    unittest.main()
