# coding: utf-8

import eikon.json_requests
from .tools import get_json_value,is_string_type, check_for_string_or_list_of_strings, check_for_string, build_dictionary, build_list, build_list_with_params
import pandas as pd


DataGrid_UDF_endpoint = 'DataGrid'


def TR_Field(field_name,params = None,sort_dir =None,sort_priority=None):
    """
    This is a helper function to build the field for the get_data function
    Returns a dictionary that can directly passed to get_data

    Parameters
    ----------
    field_name: string
    params: dictionary containing the parameters for the field passed in the argument field_name
    sort_dir: string
      Indicate the sort direction. Possible values are 'asc' or 'desc'. The default value is 'asc'
    sort_priority: integer
       Gives a piority to the field for the sorting. The highest priority is 0 (zero). the default value is None
    
    ex: 
    TR_Field('tr.revenue')
    TR_Field('tr.open','asc',1)
    TR_Field('TR.GrossProfit',{'Scale': 6, 'Curn': 'EUR'},'asc',0)

    """
    if params is not None and type(params) != dict:
        raise ValueError('TR_Field error: The argument params must be a dictionary')
    
    if type(params) == dict and not bool(params):
        raise ValueError('TR_Field error: The argument params must be a non empty dictionary or set to None (default value if not set)')

    field = {field_name:{}}
    if params:field[field_name]['params'] = params

    if sort_dir is not None:
        if is_string_type(sort_dir) and sort_dir in ['asc','desc']:
            field[field_name]['sort_dir'] = sort_dir
        else:
            raise ValueError('TR_Field error: The argument sort_dir must be a string ("asc" or "desc")')

    if sort_priority is not None:
        if type(sort_priority)is not int:
            raise ValueError('TR_Field error: The argument sort_priority must be a integer')
        field[field_name]['sort_priority'] = sort_priority
    return field


def get_data(instruments, fields, parameters=None, field_name=False, raw_output=False, debug=False):
    """
    Returns a pandas.DataFrame with fields in columns and instruments as row index

    Parameters
    ----------
    instruments: string or list
        Single instrument or list of instruments to request.

    fields: string, dictionary or list of string and/or dictionary
        - Single field as a string: 'TR.PriceClose'
        - Single field as a dictionary for providing parameters and/or sort option:  
         ex:
            {'TR.GrossProfit': { 'params':{ 'Scale': 6, 'Curn': 'EUR' }}
            {'TR.GrossProfit': { 'params':{ 'Scale': 6, 'Curn': 'EUR' },sort_dir:'desc'}
       - List of fields. Items could be strings and/or dictionaries     
           ex: 
             ['TR.PriceClose','TR.PriceOpen']
             [{'TR.PriceClose':  {'sort_dir':asc,sort_priority:1}},{'TR.PriceOpen':  {'sort_dir':asc,sort_priority:0}}
        
       You can use the function TR_Field to build the fields:
       ex:
            fields = [ek.TR_Field('tr.revenue'),ek.TR_Field('tr.open','asc',1),ek.TR_Field('TR.GrossProfit',{'Scale': 6, 'Curn': 'EUR'},'asc',0)]
            data_grid, err = ek.get_data(["IBM","MSFT.O"],fields)
       
       Tips: You can launch the Data Item Browser to discover fields and parameters
        or copy field names and parameters from TR Eikon - MS Office formulas

    parameters: string or dictionary, optional
        Single global parameter key=value or dictionary of global parameters to request.
        Default: None

    field_name: boolean
        Define if column headers are filled with field name or display names.
        If True value, field names will ube used as colmun headers. Otherwise, the full display name will be used.
        Default: False

    raw_output: boolean
        By default the output is a pandas.DataFrame.
        Set raw_output=True to get data in Json format.
        Default: False

    debug: bool
        When set to True, the json request and response are printed.
        Default: False

    Returns
    -------
    pandas.DataFrame
        Returns pandas.DataFrame with fields in columns and instruments as row index

    errors
        Returns a list of errors

    Raises
    ----------
    Exception
        If http request fails or if server returns an error
    ValueError
        If a parameter type or value is wrong

    Examples
    --------
    >>> import eikon as ek
    >>> ek.set_app_id('set your app id here')
    >>> data_grid, err = ek.get_data(["IBM", "GOOG.O", "MSFT.O"], ["TR.PriceClose", "TR.Volume", "TR.PriceLow"])
    >>> data_grid, err = ek.get_data("IBM", ['TR.Employees', {'TR.GrossProfit':{'params':{'Scale': 6, 'Curn': 'EUR'},'sort_dir':'asc'}}])
    >>> fields = [ek.TR_Field('tr.revenue'),ek.TR_Field('tr.open',None,'asc',1),ek.TR_Field('TR.GrossProfit',{'Scale': 6, 'Curn': 'EUR'},'asc',0)]
    >>> data_grid, err = ek.get_data(["IBM","MSFT.O"],fields)
    """
  
    check_for_string_or_list_of_strings(instruments, 'instruments')
    instruments = build_list(instruments, 'instruments')
    instruments = [value.upper() if value.islower() else value for value in instruments]

    if parameters:
        parameters = build_dictionary(parameters, 'parameters')

    fields = parse_fields(fields)
    fields_for_request = []
    for f in fields:
        keys =  list(f.keys())
        if len(keys) != 1: raise ValueError('get_data error: The field dictionary should contain a single key which is the field name')
        name = list(f.keys())[0]
        field_info = f[name]
        if type(field_info) != dict:
            print(("get_data error :The parameters for the file {0} should be passed in a dict".format(name)))
            return None,"The parameters for field {0} are invalid".format(name)

        field = {'name':name}
        if 'sort_dir' in list(field_info.keys()):field['sort'] = field_info['sort_dir']
        if 'sort_priority' in list(field_info.keys()):field['sortPriority'] = field_info['sort_priority']
        if 'params' in list(field_info.keys()):field['parameters'] = field_info['params']
        fields_for_request.append (field)
     
    payload = {'instruments': instruments,'fields': fields_for_request}
    if parameters: payload.update({'parameters': parameters})
    result = eikon.json_requests.send_json_request(DataGrid_UDF_endpoint, payload, debug=debug)

    if raw_output:
        return result

    return get_data_frame(result, field_name)


def parse_fields(fields):
    if is_string_type(fields): return [{fields:{}}]
    if type(fields) == dict: return [fields]
    field_list = []
    if type(fields) == list:
       for f in fields:
             if is_string_type(f):field_list.append({f:{}})
             elif type(f) == dict:field_list.append(f)
             else:raise ValueError('get_data error: the fields should be of type string or dictionary ')
       return field_list
    
    raise ValueError('get_data error: the field parameter should be a string, a dictionary , or a list of strings or/and dictionaries ')


def get_data_value(value):
    if is_string_type(value):
        return value
    elif value is dict:
        return value['value']
    else:
        return value


def get_data_frame(data_dict, field_name=False):
    if field_name:
        headers = [header.get('field', header.get('displayName')) for header in data_dict['headers'][0]]
    else:
        headers = [header['displayName'] for header in data_dict['headers'][0]]
    data = pd.np.array([[get_data_value(value) for value in row] for row in data_dict['data']])
    df = pd.DataFrame(data, columns=headers)
    df = df.apply(pd.to_numeric, errors='ignore')
    errors = get_json_value(data_dict, 'error')
    return df, errors