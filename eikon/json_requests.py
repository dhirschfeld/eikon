# coding: utf-8

import requests
import json
from .tools import is_string_type
from .eikonError import *
import eikon.Profile
import logging

def send_json_request(entity, payload, ID='123', debug=False):
    """
    Returns the JSON response.
    This function can be used for advanced usage or early access to new features.

    Parameters
    ----------
    entity: string
        A string containing a service name

    payload: string
        A string containing a JSON request

    debug: bool, optional
        When set to True, the json request and response are printed.
        Default: False

    Returns
    -------
    string
        The JSON response as a string

    Raises
    ------
    EikonError
        If daemon is disconnected

    requests.Timeout
        If request times out

    Exception
        If request fails (HTTP code other than 200)

    EikonError
        If daemon is disconnected
    """
    logger = eikon.Profile.get_profile().logger

    if debug:
        logger.debug("entity: ", entity)
        logger.debug("payload: ", payload)

    profile = eikon.Profile.get_profile()
    if profile:
        if not is_string_type(entity):
            raise ValueError('entity must be a string identifying an UDF endpoint')
        try:
            if is_string_type(payload):
                data = json.loads(payload)
            elif type(payload) is dict:
                data = payload
            else:
                raise ValueError('payload must be a string or a dictionary')
        except json.decoder.JSONDecodeError:
            raise ValueError('payload must be json well formed.')

        try:
            # build the request
            udf_request = {'Entity': {'E': entity, 'W': data}, 'ID':ID}

            if debug:
                logger.debug('Request: {}'.format(json.dumps(udf_request)))

            response = profile.get_session().post(profile.get_url(),
                                     data=json.dumps(udf_request),
                                     headers={'Content-Type': 'application/json',
                                              'x-tr-applicationid': profile.get_application_id()},
                                     timeout=60)

            if debug:
                try:
                    logger.info('HTTP Response: {} - {}'.format(response.status_code, response.text))
                except UnicodeEncodeError:
                    logger.error('HTTP Response: cannot decode error message')

            if response.status_code == 200:
                result = response.json()
                check_server_error(result)
                return result
            if response.status_code == 401:
                raise EikonError('401', response.text) #'daemon is disconnected')
            else:
                raise requests.HTTPError(str(response), response=response)

        except requests.exceptions.ConnectionError as connectionError:
             network_error = True
        if network_error:
           raise EikonError('401','Eikon Proxy not installed or not running. Please read the documentation to know how to install and run the proxy.')
             

        

def check_server_error(server_response):
    """
    Check server response.

    Check is the server response contains an HTPP error or a server error.

    :param server_response: request's response
    :type server_response: requests.Response
    :return: nothing

    :raises: Exception('HTTP error : <error_message>) if response contains HTTP response
              ex: '<500 Server error>'
          or Exception('Server error (<error code>) : <server_response>') if UDF returns an error
              ex: {u'ErrorCode': 500, u'ErrorMessage': u'Requested datapoint was not found: News_Headlines', u'Id': u''}

    """
    str_response = str(server_response)

    # check HTTPError on proxy request
    if str_response.startswith('<') and str_response.endswith('>'):
        raise requests.HTTPError(str_response, response=server_response)

    if hasattr(server_response, 'ErrorCode'):
        raise requests.HTTPError(server_response['ErrorMessage'], response=server_response)

    # check UDF error
    if 'ErrorCode' in server_response and 'ErrorMessage' in server_response:
        error_message = server_response['ErrorMessage']
        if len(error_message.split(',')) > 4:
            status, reason_phrase, version, content, headers = error_message.split(',')[:5]
            status_code = status.split(':')[1]
        else:
            status_code = server_response['ErrorCode']
        raise requests.HTTPError(error_message, response=server_response)

    # check DataGrid error
    if 'error' in server_response and 'transactionId' in server_response:
        error_message = server_response['error']
        status_code = 500
        raise requests.HTTPError(error_message, response=server_response)
