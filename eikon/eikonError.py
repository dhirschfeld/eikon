# coding: utf-8


class EikonError(Exception):
    """Base class for exceptions in this module.

    :param error_code:
    :param message: description
    """
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return repr("Error code {0} | {1} ".format(self.code, self.message))
