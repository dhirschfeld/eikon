# coding: utf-8

import eikon.json_requests, eikon.Profile
# from .Profile import Profile, get_profile
from .tools import is_string_type, to_datetime
import pandas as pd


News_Headlines_UDF_endpoint = "News_Headlines"
News_Story_UDF_endpoint = "News_Story"


def get_news_headlines(query='Topic:TOPALL and Language:LEN', count=10, date_from=None,
                       date_to=None, raw_output=False, debug=False):
    """
    Returns a list of news headlines

    Parameters
    ----------
    query: string, optional
        News headlines search criteria.
        The text can contain RIC codes, company names, country names and
        operators (AND, OR, NOT, IN, parentheses and quotes for explicit search…).

        Tip: Append 'R:' in front of RIC names to improve performance.

        Default: Top News written in English

    count: int, optional
        Max number of headlines retrieved.
        Value Range: [1-100].
        Default: 10

    date_from: string or datetime, optional
        Beginning of date range.
        String format is: '%Y-%m-%dT%H:%M:%S'. e.g. '2016-01-20T15:04:05'.

    date_to: string or datetime, optional
        End of date range.
        String format is: '%Y-%m-%dT%H:%M:%S'. e.g. '2016-01-20T15:04:05'.

    raw_output: boolean
        Set this parameter to True to get the data in json format
        if set to False, the function will return a data frame
        Default: False

    debug: bool
        When set to True, the json request and response are printed.
        Default: False

    Returns
    -------
    pandas.DataFrame
        Returns a DataFrame of news headlines with the following columns:

        - Index               : Timestamp of the publication time
        - version_created     : Date of the latest update on the news
        - text                : Text of the Headline
        - story_id            : Identifier to be used to retrieve the full story using the get_news_story function
        - source_code         : Second news identifier

    Raises
    ----------
    Exception
        If http request fails or if server returns an error
    AttributeError
        If a parameter type is wrong

    Examples
    --------
    >>> import eikon as ek
    >>> ek.set_app_id('set your app id here')
    >>> headlines = ek.get_news_headlines("R:MSFT.O", 2)
    >>> headlines
                                    versionCreated                                              text \
    2016-04-13 18:28:57.000 2.016-04-13 18:28:59.001 RBC Applies Blockchain as a Loyalty Boost<MSFT...
    2016-04-13 17:28:21.577 2016-04-13 17:28:21.671 UPDATE 2-Long-stalled email privacy bill advan...
                                                                    storyId
    2016-04-13 18:28:57.000    urn:newsml:reuters.com:20160413:nNRA1uxh03:1
    2016-04-13 17:28:21.577    urn:newsml:reuters.com:20160413:nL2N17G16Q:2

    >>> headlines = ek.get_news_headlines("R:MSFT.O IN FRANCE")
    >>> headlines = ek.get_news_headlines("R:MSFT.O IN FRANCE IN ENGLISH", count=5)
    >>> headlines = ek.get_news_headlines("OBA* OR CLINTON IN ENGLISH", count=5)
    """

    # check parameters type and values
    if not is_string_type(query):
        raise ValueError('query must be a string')

    if type(count) is not int:
        raise ValueError('count must be an integer')
    elif count < 0:
        raise ValueError('count must be equal or greater than 0')

    # build the payload
    app_id = eikon.get_app_id()
    payload = {'number': str(count), 'query': query, 'productName': app_id, 'attributionCode': ''}

    if date_from is not None:
        payload.update({'dateFrom': to_datetime(date_from).isoformat()})

    if date_to is not None:
        payload.update({'dateTo': to_datetime(date_to).isoformat()})

    result = eikon.json_requests.send_json_request(News_Headlines_UDF_endpoint, payload, debug=debug)

    if raw_output:
        return result
    else:
        return get_data_frame(result)

def get_data_frame(json_data):
    
    Headline_Selected_Fields = ['versionCreated', 'text', 'storyId', 'sourceCode']
    Headline_All_Fields_ = ['text', 'storyId', 'bodyType', 'displayDirection', 'documentType',
                             'isAlert', 'language', 'permIDs', 'products', 'rcs', 'reportCode', 'sourceCode',
                             'sourceName', 'versionCreated']
 
    json_headlines_array = json_data['headlines']
    first_created = [headline['firstCreated'] for headline in json_headlines_array]
    headlines = [[headline[field] for field in Headline_Selected_Fields]
                 for headline in json_headlines_array]
    headlines_dataframe = pd.DataFrame(headlines, pd.np.array(first_created, dtype='datetime64'), Headline_Selected_Fields)
    headlines_dataframe['versionCreated'] = headlines_dataframe.versionCreated.apply(pd.to_datetime)
    return headlines_dataframe

def get_news_story(story_id, raw_output=False, debug=False):
    """
    Return a single news story corresponding to the identifier provided in story_id

    Parameters
    ----------
    story_id:  The story id. The story id is a field you will find in every headline you retrieved with the function get_news_headlines

    raw_output: boolean
        Set this parameter to True to get the data in json format
        if set to False, the function will return returns the story content
        The default value is False

    debug: bool
        When set to True, the json request and response are printed.

    Raises
    ------
    Exception
        If http request fails or if Thomson Reuters Services return an error
    ValueError
        If a parameter type or value is wrong

    Examples
    --------
    >>> import eikon as ek
    >>> ek.set_app_id('set your app id here')
    >>> headlines = ek.get_news_headlines('IBM')
    >>> for index, headline_row in headlines.iterrows():
           story = ek.get_news_story(headline_row['storyId'])
           print (story)
    """

    app_id = eikon.get_app_id()
    payload = {'attributionCode': '', 'productName': app_id, 'storyId': story_id}
    json_data = eikon.json_requests.send_json_request(News_Story_UDF_endpoint, payload, debug=debug)

    if raw_output:
        return json_data
    else:
        return json_data['story']['storyHtml']


