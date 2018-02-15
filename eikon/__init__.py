# coding: utf-8
__version__ = "0.1.10"

"""
    eikon is a Python library to access Thomson Reuters Data with Python.
    It's usage requires:
        - An Thomson Reuters Eikon login
        - The Eikon Scripting Proxy

"""

from .Profile import set_app_id, get_app_id, set_timeout, get_timeout
from .symbology import get_symbology
from .json_requests import send_json_request
from .news_request import get_news_headlines, get_news_story
from .time_series import get_timeseries
from .data_grid import get_data, TR_Field
from .eikonError import EikonError




