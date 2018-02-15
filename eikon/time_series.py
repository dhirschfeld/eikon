# coding: utf-8

from datetime import datetime, timedelta
from dateutil.tz import tzlocal
import eikon.json_requests
from .tools import is_string_type, check_for_string_or_list_of_strings, check_for_string, check_for_int, get_json_value, \
    to_datetime, get_date_from_today
import pandas as pd
from eikon.eikonError import *
import warnings


TimeSeries_UDF_endpoint = 'TimeSeries'

Calendar_Values = ['native', 'tradingdays', 'calendardays']
Corax_Values = ['adjusted', 'unadjusted']



def get_timeseries(rics, fields='*', start_date=get_date_from_today(100), end_date=get_date_from_today(0), interval='daily', count=None,
                   calendar=None, corax=None, normalize=False, raw_output=False, debug=False):
    """
    Returns historical data on one or several RICs

    Parameters
    ----------
    rics: string or list of strings
        Single RIC or List of RICs to retrieve historical data for

    start_date: string or datetime.datetime or datetime.timedelta
        Starting date and time of the historical range.
        string format is: '%Y-%m-%dT%H:%M:%S'. e.g. '2016-01-20T15:04:05'.
        datetime.timedelta is negative number of day relative to datetime.now().
        Default: datetime.now() + timedelta(-100)
        You can use the helper function get_date_from_today, please see the usage in the examples section

    end_date: string or datetime.datetime or datetime.timedelta
        End date and time of the historical range.
        string format could be:
            '%Y-%m-%d' (e.g. '2017-01-20')
            '%Y-%m-%dT%H:%M:%S' (e.g. '2017-01-20T15:04:05')
        datetime.timedelta is negative number of day relative to datetime.now().
        Default: datetime.now()
        You can use the helper function get_date_from_today, please see the usage in the examples section

    interval: string
        Data interval.
        Possible values: 'tick', 'minute', 'hour', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly' (Default 'daily')
        Default: 'daily'

    fields: string or list of strings
        Use this parameter to filter the returned fields set.
        Available fields: 'TIMESTAMP', 'VALUE', 'VOLUME', 'HIGH', 'LOW', 'OPEN', 'CLOSE', 'COUNT'
        By default all fields are returned.

    count: int, optional
        Max number of data points retrieved.

    calendar: string, optional
        Possible values: 'native', 'tradingdays', 'calendardays'.

    corax: string, optional
        Possible values: 'adjusted', 'unadjusted'

    normalize: boolean
        if set to True, the function will return a normalized data frame with the following columns 'Date','Security','Field'
        If the value of this parameter is False the returned data frame shape will depend on the number of rics and the number of fields in the response
        There are three different shapes
        - One ric and many fields
        - Many rics and one field
        - Many rics and many fields
        Default: False
        Remark: This parameter has a less precedence than the parameter rawOutput i.e. if rawOutput is set to True, the returned data will be the raw data and this parameter will be ignored

    raw_output: boolean
        Set this parameter to True to get the data in json format
        if set to False, the function will return a data frame which shape is defined by the parameter normalize
        Default: False

    debug: bool
        When set to True, the json request and response are printed.
        Default: False

    Raises
    ------
    Exception
        If request fails or if server returns an error
    ValueError
        If a parameter type or value is wrong

    Examples
    --------
    >>> import eikon as ek
    >>> ek.set_app_id('set your app id here')
    >>> req = ek.get_timeseries(["MSFT.O"], start_date = "2017-02-01T15:04:05",
    >>>                          end_date = "2017-02-05T15:04:05", interval="tick")
    >>> req = ek.get_timeseries(["MSFT.O"], start_date = "2017-03-01",
    >>>                          end_date = "2017-03-10", interval="daily")
    >>> req = ek.get_timeseries(["MSFT.O"], start_date = get_date_from_today(150),
    >>>                          end_date = get_date_from_today(100), interval="daily")
    """

    # set the ric(s) in the payload
    check_for_string_or_list_of_strings(rics, 'rics')
    if is_string_type(rics):
        rics = [rics.strip()]

    if type(rics) == list: rics = [ric.upper() if ric.islower() else ric for ric in rics]
    payload = {'rics': rics}

    # set the field(s) in the payload
    if fields is None or fields == '*':
        fields = ['*']
    else:
        check_for_string_or_list_of_strings(fields, 'fields')
        if is_string_type(fields):
            fields = fields.strip().upper().split()
        else:
            fields = [x.upper() for x in fields]

    if '*' in fields:
        fields = ['*']
    elif 'TIMESTAMP' not in fields:
        fields.append('TIMESTAMP')

    # check the interval in the payload
    check_for_string(interval, 'interval')

    start_date = to_datetime(start_date).isoformat()
    end_date = to_datetime(end_date).isoformat()

    if start_date > end_date: raise ValueError('end date should be after than start date ')

    payload = {'rics': rics, 'fields': fields, 'interval': interval, 'startdate': start_date, 'enddate': end_date}

    # Add optional parameters

    # set the count in the payload
    if count is not None:
        check_for_int(count, 'count')
        payload.update({'count': count})

    # set the calendar in the payload
    if calendar is not None:
        if is_string_type(calendar):
            payload.update({'calendar': calendar})
        else:
            raise ValueError('calendar must be a string')

    # set the corax in the payload
    if corax is not None:
        if is_string_type(corax):
            payload.update({'corax': corax})
        else:
            raise ValueError('corax must be a string')

    ts_result = eikon.json_requests.send_json_request(TimeSeries_UDF_endpoint, payload, debug=debug)

    # Catch all errors to raise a warning
    ts_timeserie_data = ts_result['timeseriesData']
    ts_status_errors = [ts_data for ts_data in ts_timeserie_data if get_json_value(ts_data ,'statusCode')=='Error']

    ts_error_messages = ''
    for ts_status in ts_status_errors:
        ts_error_message = get_json_value(ts_status, 'errorMessage')
        ts_error_message = ts_error_message[ts_error_message.find("Description"):]
        ts_instrument = get_json_value(ts_status, 'ric')
        ts_error_message = ts_error_message.replace('Description', ts_instrument)
        ts_error_messages += ts_error_message
        ts_error_messages += ' | '
        warning_message = 'Error with {0}'.format(ts_error_message)
        warnings.warn(warning_message)

    #  if all timeseries are in error, then raise EikonError with all error messages
    if len(ts_status_errors)==len(ts_timeserie_data):
        raise EikonError('Error', message=ts_error_messages)

    if raw_output: return ts_result

    data_frame = None
    if normalize:
        data_frame = NormalizedDataFrame_Formatter(ts_result).get_data_frame()
    else:
        data_frame = NiceDataFrame_Formatter(ts_result).get_data_frame()

    if len(data_frame) > 0:
        data_frame = data_frame.fillna(pd.np.nan)
    return data_frame


class NormalizedDataFrame_Formatter():
    def __init__(self, json_data):
        self.json_data = json_data

    def get_data_frame(self):
        timeseriesList = self.json_data['timeseriesData']
        data_dict_list = []
        for timeseries in timeseriesList:
            ric = timeseries['ric']
            error_code = timeseries['statusCode']
            if error_code.lower() == 'error':
                continue

            fields = [f['name'] for f in timeseries['fields']]
            timestamp_index = fields.index('TIMESTAMP')
            fields.pop(timestamp_index)  # remove timestamp from fields (timestamp is used as index for dataframe)
            datapoints = pd.np.array(timeseries['dataPoints'])
            timestamps = pd.np.array(datapoints[:, timestamp_index], dtype='datetime64')  # index for dataframe
            datapoints = pd.np.delete(datapoints, pd.np.s_[timestamp_index], 1)  # remove timestamp column from numpy array
            fiels_count = len(fields)
            column_size = len(datapoints)
            symbol_column = pd.np.array([ric] * fiels_count * column_size)
            fields_column = pd.np.array(fields * column_size)
            values_column = pd.np.concatenate(datapoints, axis=0)
            timestamp_column = [[timestamps[i]] * fiels_count for i in range(timestamps.size)]
            timestamp_column = pd.np.concatenate(timestamp_column, axis=0)
            data_dict_list.append(
                dict(Date=timestamp_column, Security=symbol_column, Field=fields_column, Value=values_column))

        data_frames = [pd.DataFrame(data_dict, dtype='float') for data_dict in data_dict_list]
        return pd.concat(data_frames)


class NiceDataFrame_Formatter():
    def __init__(self, json_data):
        self.json_data = json_data

    def get_data_frame(self):
        data_frames, rics, fields = self._get_frame_list()
        rics_count = len(rics)
        fields_count = len(fields)
        if rics_count == 0 or fields_count == 0:
            return data_frames
        if rics_count == 1: return self._get_frame_1_ric_N_fields(data_frames, rics[0])
        if rics_count > 1 and fields_count == 1: return self._get_frame_N_rics_1_field(data_frames, rics, fields[0])
        return self._get_frame_N_rics_N_fields(data_frames, rics, fields)

    def _get_frame_list(self):
        timeseriesList = self.json_data['timeseriesData']
        data_frames = []
        unique_fields = []
        rics = []
        for timeseries in timeseriesList:
            ric = timeseries['ric']
            error_code = timeseries['statusCode']
            if error_code.lower() == 'error':
                continue

            rics.append(ric)
            fields = [f['name'] for f in timeseries['fields']]
            timestamp_index = fields.index('TIMESTAMP')
            fields.pop(timestamp_index)  # remove timestamp from fields (timestamp is used as index for dataframe)
            unique_fields = fields
            datapoints = pd.np.array(timeseries['dataPoints'])
            timestamps = pd.np.array(datapoints[:, timestamp_index], dtype='datetime64')  # index for dataframe
            datapoints = pd.np.delete(datapoints, pd.np.s_[timestamp_index], 1)  # remove timestamp column from numpy array
            df = pd.DataFrame(datapoints, columns=fields, index=timestamps, dtype='float')
            df.index.name = 'Date'
            data_frames.append(df)

        return data_frames, list(rics), list(unique_fields)

    def _get_frame_1_ric_N_fields(self, data_frames, ricName):
        data_frame = pd.concat(data_frames, axis=1)
        data_frame.axes[1].name = ricName
        return data_frame

    def _get_frame_N_rics_1_field(self, data_frames, rics, fieldName):
        ric_index = 0
        for df in data_frames:
            ric_name = rics[ric_index]
            df.rename(columns={fieldName: ric_name}, inplace=True)
            ric_index += 1
        data_frame = pd.concat(data_frames, axis=1)
        data_frame.axes[1].name = fieldName
        return data_frame

    def _get_frame_N_rics_N_fields(self, data_frames, rics, fields):
        ric_index = 0
        for df in data_frames:
            ric_name = rics[ric_index]
            columns = [(ric_name, f) for f in fields]
            df.columns = pd.MultiIndex.from_tuples(columns)
            ric_index += 1
        data_frame = pd.concat(data_frames, axis=1)
        data_frame.axes[1].names = ['Security', 'Field']
        return data_frame
