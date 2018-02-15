# coding: utf-8

import os
from appdirs import *
import platform
from requests import Session
from requests.exceptions import ConnectTimeout
from .eikonError import *
from .tools import is_string_type
import socket

# global profile
profile = None


def set_app_id(app_id):
    """
    Set the application id.

    Parameters
    ----------
    app_id : string
        the application id

    Notes
    -----
    The application ID identifies your application on Thomson Reuters Platform.
    You can get an application ID using the Application ID generator. This App can
    be launched from TR Eikon Proxy welcome page.
    """
    global profile
    profile = Profile(app_id)


def get_app_id():
    """
    Returns the application ID previously set

    Notes
    -----
    The application ID identifies your application on Thomson Reuters Platform.
    You can get an application ID using the Application ID generator. This App can
    be launched from TR Eikon Proxy welcome page.
    """
    if profile is None:
        raise EikonError('401','AppID is missing. Did you forget to call set_app_id()?')

    return profile.get_application_id()


def set_timeout(timeout):
    """
    Set the timeout for each request.

    Parameters
    ----------
    timeout : int
        the request timeout in msec
    """
    get_profile().set_timeout(timeout)


def get_timeout():
    """
    Returns the request timeout in msec
    """
    if profile is None:
        raise EikonError('401','AppID is missing. Did you forget to call set_app_id()?')

    return profile.get_timeout()


def set_port_number(port_number):
    """
    Set the port number to reach Eikon API proxy.

    Parameters
    ----------
    port_number : int
        the port number
    """
    get_profile().set_port_number(port_number)


def get_port_number():
    """
    Returns the port number
    """
    if profile is None:
        raise EikonError('401','AppID is missing. Did you forget to call set_app_id()?')

    return profile.get_port_number()


def get_profile():
    """
    Returns a Profile class containing the EPAID
    """
    if profile is None:
        raise EikonError('401','AppID is missing. Did you forget to call set_app_id()?')

    return profile


class Profile(object):
    def __init__(self, application_id):
        """
        Initialization of the profile.

        :param application_id:
        :type application_id: StringTypes
        """
        if not is_string_type(application_id):
            raise AttributeError('application_id must be a string')

        self.session = Session()
        self.session.trust_env = False
        self.application_id = application_id
        self.port = identify_scripting_proxy_port(self.session, self.application_id)
        self.url = "http://localhost:{0}/api/v1/data".format(self.port)
        self.streaming_url = "ws://localhost:{0}/?".format(self.port)
        self.timeout = 30

    def get_application_id(self):
        """
        Returns the application id.
        """
        if not self.application_id:

            raise EikonError('401','AppID was not set (set_app_id was not called)')
        return self.application_id

    def get_url(self):
        """
        Returns the scripting proxy url.
        """
        return self.url

    def get_streaming_url(self):
        """
        Returns the streaming proxy url.
        """
        return self.streaming_url

    def get_session(self):
        """
        Returns the scripting proxy session for requests.
        """
        return self.session

    def set_timeout(self, timeout):
        """
        Set the timeout for requests.
        """
        self.timeout = timeout

    def get_timeout(self):
        """
        Returns the timeout for requests.
        """
        return self.timeout

    def set_port_number(self, port_number):
        """
        Set the port number to reach Eikon API proxy.
        """
        self.port = port_number

    def get_port_number(self):
        """
        Returns the port number
        """
        return self.port


def read_firstline_in_file(filename):
    try:
        f = open(filename)
        first_line = f.readline()
        f.close()
        return first_line
    except IOError as e:
        print('I/O error({0}): {1}'.format(e.errno, e.strerror))
        return ''


def identify_scripting_proxy_port(session, application_id):
    """
    Returns the port used by the Scripting Proxy stored in a configuration file.
    """

    port = None

    app_names = ['Eikon API proxy', 'Eikon Scripting Proxy']
    app_author = 'Thomson Reuters'

    if platform.system() == 'Linux':
        path = [user_config_dir(app_name, app_author, roaming=True)
                for app_name in app_names if os.path.isdir(user_config_dir(app_name, app_author, roaming=True))]
    else:
        path = [user_data_dir(app_name, app_author, roaming=True)
                for app_name in app_names if os.path.isdir(user_data_dir(app_name, app_author, roaming=True))]

    if len(path):
        port_in_use_file = os.path.join(path[0], '.portInUse')

        # Test if '.portInUse' file exists
        if os.path.exists(port_in_use_file):
            # First test to read .portInUse file
            firstline = read_firstline_in_file(port_in_use_file)
            if firstline != '':
                port = firstline.strip()
                print('Port {0} was retrieved from .portInUse file'.format(port))

    if port is None:
        print('Warning: file .portInUse was not found.\n         Try to fallback to default port number.')
        port_list = ['36036', '9000']
        for port_number in port_list:
            print('Try defaulting to port {0}...'.format(port_number))
            if check_port(session, application_id, port_number, timeout=1):
                return port_number

    if port is None:
        print('Error: no proxy address identified. Check if Eikon Desktop or Eikon API Proxy is running .')

    return port

def check_port(session, application_id, port, timeout=1.0):
    url = "http://localhost:{0}/api/v1/data".format(port)
    try:
        response = session.get(url,
                            headers = {'x-tr-applicationid': application_id},
                            timeout=timeout)

        print('Response : {0} - {1}'.format(response.status_code, response.text))
        print('Port {0} is detected'.format(port))
        return True
    except (socket.timeout, ConnectTimeout):
        print('Timeout on checking port {0}'.format(port))
    except Exception as e:
        print('Error on checking port {0} : {1}'.format(port, e.__str__()))
    return False
