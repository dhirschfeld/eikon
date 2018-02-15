# coding: utf-8
from datetime import date, datetime, timedelta
from dateutil.tz import tzlocal
import dateutil.parser
import json


def is_string_type(value):
    try:
        return isinstance(value, basestring)
    except NameError:
        return isinstance(value, str)


def get_json_value(json_data, name):
    if name in json_data:
        return json_data[name]
    else:
        return None


def to_datetime(date_value):
    if type(date_value) is timedelta:
        return datetime.now(tzlocal()) + date_value

    if type(date_value) in (datetime, date):
        return date_value

    try:
        return dateutil.parser.parse(date_value)
    except ValueError as e:
        raise e
    except Exception as e:
        raise ValueError(e)



def get_date_from_today(days_count): 
    if type(days_count) != int :
        raise ValueError('The parameter {0} should be an integer, found {1}'.format(days_count,type(days_count)))
    return datetime.now(tzlocal()) + timedelta(days=-days_count)


def is_list_of_string(values):
  return all(is_string_type(value) for value in values)


def check_for_string(parameter, name):
    if not is_string_type(parameter):
        raise ValueError('The parameter {0} should be a string, found {1}'.format(name,str(parameter)))


def check_for_string_or_list_of_strings(parameter, name):
    if type(parameter) != list and (not parameter or not is_string_type(parameter)):
        raise ValueError('The parameter {0} should be a string or a list of string, found {1}'.format(name,type(parameter)))
    if type(parameter) == list and not is_list_of_string(parameter): 
        raise ValueError('All items in the parameter {0} should be of data type string, found {0}'.format(name,[type(v) for v in parameter]))


def check_for_int(parameter, name):
    if type(parameter) is not int:
        raise ValueError('The parameter {0} should be an int, found {1} type value ({2})'.format(name, type(parameter), str(parameter)))


def build_list_with_params(values, name):
    if values is None:
        raise ValueError(name + ' is None, it must be a string or a list of strings')

    if is_string_type(values):
        return [(v, None) for v in values.split()]
    elif type(values) is list:
        try:
            return [(value, None) if is_string_type(value) else (value[0], value[1]) for value in values]
        except Exception:
            raise ValueError(name + ' must be a string or a list of strings or a tuple or a list of tuple')
    else:
        try:
            return values[0], values[1]
        except Exception:
            raise ValueError(name + ' must be a string or a list of strings or a tuple or a list of tuple')


def build_list(values, name):
    if values is None:
        raise ValueError(name + ' is None, it must be a string or a list of strings')

    if is_string_type(values):
        return [values.strip()]
    elif type(values) is list:
        if all(is_string_type(value) for value in values):
            return [value for value in values]
        else:
            raise ValueError(name + ' must be a string or a list of strings')
    else:
        raise ValueError(name + ' must be a string or a list of strings')


def build_dictionary(dic, name):
    if dic is None:
        raise ValueError(name + ' is None, it must be a string or a dictionary of strings')

    if is_string_type(dic):
        return json.loads(dic)
    elif type(dic) is dict:
        return dic
    else:
        raise ValueError(name + ' must be a string or a dictionary')
