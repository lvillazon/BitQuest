""" handles console output messages for debugging """
from constants import MSG_VERBOSITY


def console_msg(message, verbosity = 9, line_end='\n'):
    """ displays console messages
    if verbosity < MSG_VERBOSITY """

    if verbosity < MSG_VERBOSITY:
        print("MSG[", verbosity, "] ", message, sep='', end=line_end)