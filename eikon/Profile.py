# coding: utf-8
from appdirs import *
import platform
from requests import Session
from requests.exceptions import ConnectTimeout
from .eikonError import *
from .tools import is_string_type
import socket
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

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
    get_profile().set_application_id(app_id)


def get_app_id():
    """
    Returns the application ID previously set

    Notes
    -----
    The application ID identifies your application on Thomson Reuters Platform.
    You can get an application ID using the Application ID generator. This App can
    be launched from TR Eikon Proxy welcome page.
    """
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
    return profile.get_port_number()


def get_profile():
    """
    Returns a Profile class containing the EPAID
    """
    global profile
    if profile is None:
        profile = Profile()
    return profile


def set_log_level(level):
    """
    Set the log level.

    Parameters
    ----------
    level : int
        Possible values from logging module : [CRITICAL, FATAL, ERROR, WARNING, WARN, INFO, DEBUG, NOTSET]
    """
    get_profile().logger.setLevel(level)


class Profile(object):
    def __init__(self, application_id = None):
        """
        Initialization of the profile.

        :param application_id:
        :type application_id: StringTypes
        """

        self.log_path = None
        self.logger = logging.getLogger('pyeikon')
        self.logger.setLevel(logging.NOTSET)

        self.session = Session()
        self.session.trust_env = False
        self.port = None
        self.url = None
        self.streaming_url = None

        self.set_application_id(application_id)
        self.set_timeout(30)

    def set_application_id(self, app_id):
        """
        Set the application id.
        """
        if app_id is None:
            return

        if not is_string_type(app_id):
            raise AttributeError('application_id must be a string')

        self.application_id = app_id
        self.set_port_number(identify_scripting_proxy_port(self.session, self.application_id))
        self.logger.info('Application ID: {0}'.format(self.application_id))

    def get_application_id(self):
        """
        Returns the application id.
        """
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
        self.logger.info('Set timeout to {0} seconds'.format(self.timeout))

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
        if port_number is not None:
            self.url = "http://localhost:{0}/api/v1/data".format(self.port)
        else:
            self.url = None

        self.logger.info('Set Proxy port number to {}'.format(self.port))

    def get_port_number(self):
        """
        Returns the port number
        """
        return self.port

    def set_log_path(self, log_path):
        """
        Set the path where log file will be created.

        Parameters
        ----------
        log_path : path directory
        Default: current directory (beside *.py running file)
        """
        self.log_path = log_path

    def set_log_level(self, log_level):
        """
        Set the log level.

        Parameters
        ----------
        level : int
            Possible values from logging module : [CRITICAL, FATAL, ERROR, WARNING, WARN, INFO, DEBUG, NOTSET]
        """

        if log_level > logging.NOTSET:
            __formatter = logging.Formatter("%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s \n")
            __filename = 'pyeikon.{0}.log'.format(datetime.now().strftime('%Y%m%d.%H-%M-%S'))

            if self.log_path is not None:
                if not os.path.isdir(self.log_path):
                    os.makedirs(self.log_path)
                __filename = os.path.join(self.log_path, __filename)

            __handler = logging.handlers.RotatingFileHandler(__filename, mode='a', maxBytes=100000,
                                                        backupCount=10, encoding='utf-8')
            __handler.setFormatter(__formatter)
            self.logger.addHandler(__handler)

        self.logger.setLevel(log_level)

    def get_log_level(self):
        """
        Returns the log level
        """
        return self.logger.level


def read_firstline_in_file(filename):
    logger = get_profile().logger
    try:
        f = open(filename)
        first_line = f.readline()
        f.close()
        return first_line
    except IOError as e:
        logger.error('I/O error({0}): {1}'.format(e.errno, e.strerror))
        return ''


def identify_scripting_proxy_port(session, application_id):
    """
    Returns the port used by the Scripting Proxy stored in a configuration file.
    """

    port = None
    logger = get_profile().logger
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
                saved_port = firstline.strip()
                if check_port(session, application_id, saved_port):
                    port = saved_port
                    logger.info('Port {0} was retrieved from .portInUse file'.format(port))

    if port is None:
        logger.info('Warning: file .portInUse was not found. Try to fallback to default port number.')
        port_list = ['9000', '36036']
        for port_number in port_list:
            logger.info('Try defaulting to port {0}...'.format(port_number))
            if check_port(session, application_id, port_number):
                return port_number

    if port is None:
        logger.error('Error: no proxy address identified.\nCheck if Eikon Desktop or Eikon API Proxy is running.')

    return port


def check_port(session, application_id, port, timeout=(1.0,2.0)):
    logger = get_profile().logger
    url = "http://localhost:{0}/api/v1/data".format(port)
    try:
        response = session.get(url,
                            headers = {'x-tr-applicationid': application_id},
                            timeout=timeout)

        logger.info('Response : {0} - {1}'.format(response.status_code, response.text))
        logger.info('Port {0} is detected'.format(port))
        return True
    except (socket.timeout, ConnectTimeout):
        logger.error('Timeout on checking port {0}'.format(port))
    except Exception as e:
        logger.error('Error on checking port {0} : {1}'.format(port, e.__str__()))
    return False
