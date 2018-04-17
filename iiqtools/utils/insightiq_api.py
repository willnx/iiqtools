# -*- coding: UTF-8 -*-
"""
This module is for performing privileged API calls to InsightIQ.
"""
import collections
from threading import Lock

import requests

class ConnectionError(Exception):
    """Unable to establish an connection to the OneFS API"""
    pass


class InsightiqApi(object):
    """An authenticated connection to the InsightIQ API

    This object is a simple wrapper around a `requests Session <http://docs.python-requests.org/en/master/user/advanced/#session-objects>`_.
    The point of wrapping the requests Session object is to remove boiler plate
    code in making API calls to InsightIQ, and to auto-handle authenticating
    to the API. The most noteworthy changes to this object and how you use the
    requests Session object is that you *must* provide the username and password
    when instantiating the object, and when you make a request, you only supply
    the URI end point (i.e. not the `http://my-host.org:8080` part).

    Supports use of ``with`` statements, which will automatically handle creating
    and closing the HTTP session with InsightIQ.

    Example::

        >>> with InsightiApi(username='administrator', password='foo') as iiq:
                response = iiq.get('/api/clusters')

    :param username: **Required** The name of the administrative account for InsightIQ
    :type username: String

    :param password: **Required** The password for the administrative account being used.
    :type password: String

    :param verify: Perform SSL/TLS cert validation using system certs. Setting
                   to True will likely cause issues when using a self-signed SSL/TLS cert.
                   Default is False.
    :type verify: Boolean
    """
    def __init__(self, username, password, verify=False):
        self._username = username
        self._password = password
        self.verify = verify
        self._url = 'https://localhost/' # 127.0.0.1 would break if IPv4 is disabled
        self._session = None
        self.renew_session()

    def renew_session(self):
        """Create a new session to the InsightIQ API

        :Returns: requests.Session

        :Raises: ConnectionError

        The InsightIQ API can be a bit fickle, so this method automatically retries
        establishing upwards of 3 times.
        """
        retries = 3
        count = 0
        for attempt in range(retries):
            try:
                iiq_session = self._get_session()
            except requests.exceptions.ConnectionError:
                continue
            else:
                self._session = iiq_session
                break
        else:
            raise ConnectionError('Unable to connect to InsightIQ API')

    def _get_session(self):
        """Obtain an authentication token being used for API calls"""
        s = requests.Session()
        resp = s.post(self._url + 'login', verify=self.verify,
                      data={'username' : self._username,
                            'password' : self._password,
                            'authform' : '+Log+in+'})
        resp.raise_for_status()
        return s

    def end_session(self):
        """Logout of InsightIQ and close the connection to the server"""
        # use of with statement might result in no session created, but still call this method
        if self._session:
            try:
                self.get(self._url + '/logout')
            except requests.exceptions.ConnectionError:
                pass
            finally:
                self._session.close()

    def get(self, endpoint, params=None, data=None, headers=None, **kwargs):
        """Perform an HTTP GET request

        :Returns: PyObject

        :param endpoint: **Required** The URI end point of the InsightIQ API to call
        :type endpoint: String

        :param params: The HTTP parameters to send in the HTTP request
        :type params: Dictionary

        :param data: The HTTP body content to send in the request. The Python
                     object supplied (i.e. list, dict, etc) will be auto-converted
                     to JSON string.
        :type data: PyObject

        :param headers: Any additional HTTP headers to send in the request
        :type headers: Dictionary
        """
        return self._call(endpoint, method='get', params=params, data=data, headers=headers, **kwargs)

    def post(self, endpoint, params=None, data=None, headers=None, **kwargs):
        """Perform an HTTP POST request

        :Returns: PyObject

        :param endpoint: **Required** The URI end point of the InsightIQ API to call
        :type endpoint: String

        :param params: The HTTP parameters to send in the HTTP request
        :type params: Dictionary

        :param data: The HTTP body content to send in the request. The Python
                     object supplied (i.e. list, dict, etc) will be auto-converted
                     to JSON string.
        :type data: PyObject

        :param headers: Any additional HTTP headers to send in the request
        :type headers: Dictionary
        """
        return self._call(endpoint, method='post', params=params, data=data, headers=headers, **kwargs)

    def put(self, endpoint, params=None, data=None, headers=None, **kwargs):
        """Perform an HTTP PUT request

        :Returns: PyObject

        :param endpoint: **Required** The URI end point of the InsightIQ API to call
        :type endpoint: String

        :param params: The HTTP parameters to send in the HTTP request
        :type params: Dictionary

        :param data: The HTTP body content to send in the request. The Python
                     object supplied (i.e. list, dict, etc) will be auto-converted
                     to JSON string.
        :type data: PyObject

        :param headers: Any additional HTTP headers to send in the request
        :type headers: Dictionary
        """
        return self._call(endpoint, method='put', params=params, data=data, headers=headers, **kwargs)

    def delete(self, endpoint, params=None, data=None, headers=None, **kwargs):
        """Perform an HTTP DELETE request

        :Returns: PyObject

        :param endpoint: **Required** The URI end point of the InsightIQ API to call
        :type endpoint: String

        :param params: The HTTP parameters to send in the HTTP request
        :type params: Dictionary

        :param data: The HTTP body content to send in the request. The Python
                     object supplied (i.e. list, dict, etc) will be auto-converted
                     to JSON string.
        :type data: PyObject

        :param headers: Any additional HTTP headers to send in the request
        :type headers: Dictionary
        """
        return self._call(endpoint, method='delete', params=params, data=data, headers=headers, **kwargs)

    def head(self, endpoint, params=None, data=None, headers=None, **kwargs):
        """Perform an HTTP HEAD request

        :Returns: PyObject

        :param endpoint: **Required** The URI end point of the InsightIQ API to call
        :type endpoint: String

        :param params: The HTTP parameters to send in the HTTP request
        :type params: Dictionary

        :param data: The HTTP body content to send in the request. The Python
                     object supplied (i.e. list, dict, etc) will be auto-converted
                     to JSON string.
        :type data: PyObject

        :param headers: Any additional HTTP headers to send in the request
        :type headers: Dictionary
        """
        return self._call(endpoint, method='head', params=params, data=data, headers=headers, **kwargs)

    def _call(self, endpoint, method, **kwargs):
        """Actually makes the HTTP API calls

        The point of this abstraction is to keep our interactions with the
        `Requests <http://docs.python-requests.org>`_ library more D.R.Y.

        :Returns: requests.Response

        :param endpoint: **Required** The URI end point of the InsightIQ API to call
        :type endpoint: String

        :param method: **Required** The HTTP method to invoke.
        :type method: String

        :param **kwargs: The key/value arguments for parameters, body, and headers.
        :type **kwargs: Dictionary
        """
        caller = getattr(self._session, method)
        uri = self._build_uri(endpoint)
        return caller(uri, verify=self.verify, **kwargs)

    def _build_uri(self, endpoint):
        """Convert the supplied URI end point to a full URI

        :Returns: String

        :param endpoint: The URI resource to call
        :type endpoint: String
        """
        if endpoint.startswith('/'):
            return self._url + endpoint[1:]
        else:
            return self._url + endpoint

    def __enter__(self):
        """Enables use of ``with`` statement

        Example::

          with InsightiqApi(username='bob', password='1234') as iiq_api:
              response = iiq_api.get('some/endpoint', params={'verbose' : True})
        """
        return self

    def __exit__(self, exec_type, exec_value, the_traceback):
        self.end_session()

    @property
    def username(self):
        # Setter so derps cannot change the username
        return self._username


class Parameters(collections.MutableMapping):
    """Object for working with HTTP query parameters

    This object supports the Python dictionary API, and lets you define the same
    HTTP query parameter more than once. Additional definitions for the same
    query parameter creates a new entry in the underlying list. This decision
    makes it simple to iterate Parameters to build up the HTTP query string because
    you do not have to iterate parameter values. Because you can define the same
    parameter more than once, using the standard dictionary API will only impact
    the first occurrence of that parameter. To modify a specific parameter, you
    must use the methods in this class which extend the dictionary API.

    This documentation is specific to how Parameters extends the normal Python
    dictionary API. For documentation about the Python dictionary API, please
    checkout their official page `here <https://docs.python.org/3/library/stdtypes.html#dict>`_.

    Example creating duplicate parameters::

        >>> params = Parameters()
        >>> for value in range(3):
        ...     params.add('myParam', value)
        ...
        Parameters([['myParam', 0], ['myParam', 1], ['myParam', 2]])

    What **NOT** to do::

        >>> params = Parameters()
        >>> for doh in range(3):
        ...     params['homer'] = doh
        ...
        >>> params
        Parameters([['homer', 2], ['homer', 2], ['homer', 2]])

    Iterating Parameters to build a query string::

        >>> query = []
        >>> params = Parameters(one=1, two=2)
        >>> for name, value in params.items():
        ...     query.append('%s=%s' % (name, value))
        ...
        >>> query_str = '&'.join(query)
        >>> query_str
        'one=1&two=2'


    :param args: Data to initialize the Parameters object with.
    :type args: List, Tuple, or Dictionary

    :param kwargs: Data to initialize the Parameters object with.
    :type kwargs: Dictionary
    """
    # Indexes for what a key and value are; avoids magic numbers
    _KEY = 0
    _VAL = 1

    def __init__(self, *args, **kwargs):
        self._data = []
        self._lock = Lock()
        # iterate the args first so we can fail as shallow as possible
        for arg in args:
            if isinstance(arg, collections.Mapping):
                self._add_dict(arg)
                continue
            element, ok = self._arg_is_ok(arg)
            if ok:
                self._add_arg(arg)
            else:
                msg = 'Invalid element %s in arg %s' % (element, arg)
                raise ValueError(msg)
        # Now add any keyword args
        self._add_dict(kwargs)

    @property
    def NAME(self):
        """The array index for a parameter name; avoids magic numbers"""
        return self._KEY

    @property
    def VALUE(self):
        """The array index for a parameter value; avoids magic numbers"""
        return self._VAL

    def _add_dict(self, the_dictionary):
        """Update the Parameters object with the contents of a dictionary

        :Returns: None

        :param the_dictionary: **Required** The dictionary to add to the Parameters object
        :type the_dictionary: Dictionary
        """
        for key, value in the_dictionary.items():
            self._data.append([key, value])

    def _add_arg(self, the_arg):
        """Add the argument data to Parameters

        :param the_arg: **Required** The specific argument (from __init__) to add
        :type the_arg: List, Tuple, or Dictionary
        """
        for element in the_arg:
            if isinstance(element, collections.Mapping):
                self._add_dict(element)
            else:
                self._data.append(list(element)) # Cast everything to list, b/c it might be a tuple

    def _arg_is_ok(self, the_arg):
        """Test that the argument data structure is valid for Parameters

        :param the_arg: **Required** The argument to test
        :type the_arg: PyObject
        """
        for element in the_arg:
            if isinstance(element, collections.Mapping):
                continue
            if not (isinstance(element, tuple) or isinstance(element, list)):
                return element, False
            # query parameters are key/value pairs, so only 2 elements makes sense
            if len(element) != 2:
                return element, False
        else:
            return None, True

    def __repr__(self):
        """A human friendly representation of the Parameters object"""
        return 'Parameters(%s)' % self._data

    def __getitem__(self, param):
        """Return the parameter name.

        :param param: **Required** The name of the parameter
        :type param: String
        """
        found = [x[self._VAL] for x in self._data if x[self._KEY] == param]
        if found:
            return found[0]
        else:
            raise KeyError('No such parameter: %s' % param)

    def items(self):
        """Iterate Parameters, and return the param/value pairs

        :Returns: Generator
        """
        for pair in self._data:
            yield tuple(pair)

    def __iter__(self):
        """Iterate the parameters and return the parameter name.

        This approach makes Parameters behave like a standard Python dict()
        """
        for pair in self._data:
            yield pair[self._KEY]

    def __len__(self):
        """The number of parameters"""
        return len(self._data)

    def __setitem__(self, key, value):
        """Create or update a parameter

        If you want to add a duplicate parameter, use the ``.add()`` method

        :param key: **Required** The parameter to create or update
        :type key: String

        :param value: **Required** The value for the parameter
        :type value: PyObject
        """
        for pair in self._data:
            if pair[self._KEY] == key:
                pair[self._VAL] = value
        else:
            self._data.append([key, value])

    def __delitem__(self, key):
        """Delete the first occurrence of a parameter

        :Raises: KeyError - when parameter does not exist

        :Returns: None

        :param key: **Required** The name of the parameter to delete
        :type key: String
        """
        for index, pair in enumerate(self._data):
            if pair[self._KEY] == key:
                value = self._data.pop(index)[self._VAL]
                return value
        else:
            msg = 'No such parameter: %s' % key
            raise KeyError(msg)

    def _find_occurrence_index(self, name, occurrence):
        """Return the index of the N-th occurrence of a recurring parameter

        :Raises: KeyError - if param or occurrence doesn't exist

        :Returns: Integer

        :param name: **Required** The name of the parameter to locate
        :type name: String

        :param occurrence: **Required** The N-th instance the parameter is defined. Zero-based numbering.
        :type occurrence: Integer
        """
        count = 0
        param_exists = False
        for index, pair in enumerate(self._data):
            if pair[self._KEY] == name:
                param_exists = True
                if count == occurrence:
                    return index
                else:
                    count += 1
        # Param or occurrence not found :(
        if param_exists:
            msg = 'Parameter %s does not have an occurrence of %s' % (name, occurrence)
        else:
            msg = 'No such parameter: %s' % name
        raise KeyError(msg)

    def add(self, name, value):
        """Add a duplicate parameter

        :Returns: None

        :param name: **Required** The name of the parameter
        :type name: String

        :param value: **Required** The value for the duplicate parameter
        :type value: PyObject
        """
        self._data.append([name, value])

    def delete_parameter(self, name, occurrence):
        """Delete a specific parameter that is defined more than once. Thread safe.

        :Returns: None

        :param name: **Required** The parameter to delete.
        :type name: String

        :param occurrence: **Required** The N-th instance of a parameter. Zero based numbering.
        :type occurrence: Integer
        """
        self._lock.acquire()
        try:
            index = self._find_occurrence_index(name, occurrence)
            self._data.pop(index)
        finally:
            self._lock.release()

    def modify_parameter(self, name, new_value, occurrence):
        """Change the value of a specific parameter that is defined more than once.
        Thread safe.

        :Returns: None

        :param name: **Required** The parameter to delete.
        :type name: String

        :param new_value: **Required** The value for the parameter
        :type new_value: PyObject

        :param occurrence: **Required** The N-th instance of a parameter. Zero based numbering.
        :type occurrence: Integer
        """
        self._lock.acquire()
        try:
            index = self._find_occurrence_index(name, occurrence)
            self._data[index] = [name, new_value]
        finally:
            self._lock.release()

    def get_all(self, name):
        """Return the key/value pairs for a parameter. Order is maintained.

        :Returns: List

        :param name: **Required** The name of the query parameter
        :type name: String
        """
        return [x for x in self._data if x[self._KEY] == name]
