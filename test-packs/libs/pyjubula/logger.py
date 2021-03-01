"""
------------------------------------------------------------------------------------------------------------------------
    PyJubula :: logger.py
------------------------------------------------------------------------------------------------------------------------

    This module contains logging class customization.

    (c) 2015 by the OXES QA Team

------------------------------------------------------------------------------------------------------------------------
"""

import logging
from platform import system
if system() == 'Windows':
    from ctypes import windll
from .constant import CONSOLE_MESSAGES

logging.basicConfig(format='{asctime} {name:8s} -> {levelname:8s}:: {message}', style='{', datefmt='%Y-%m-%d %I:%M:%S')


class Logger:
    """
    --------------------------------------------------------------------------------------------------------------------
    Class that customizes logging.
    Uses the CONSOLE_MESSAGES constant.
    --------------------------------------------------------------------------------------------------------------------
    """

    COLORS = {'EXCEPTION': 0x0004, 'FATAL': 0x0004, 'ERROR': 0x0004, 'WARNING': 0x0006, 'INFO': 0x0002, 'DEBUG': 0x0008,
              'DEFAULT': 0x0007}

    def __init__(self, name, log_level):
        """
        ----------------------------------------------------------------------------------------------------------------
        Initialize logging for a class specified by name.
        Args:
            name        (str):   name of class that should be logging,
            log_level   (int):   the desired logging level.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._logger = logging.getLogger(str(name))
        if log_level not in [10, 20, 30, 40]:
            self._logger.setLevel(logging.INFO)
            self.write("LOGGER_INVALID_LEVEL")
        else:
            self._logger.setLevel(log_level)

    def write(self, *params):
        """
        ----------------------------------------------------------------------------------------------------------------
        Writes a message into a log from the CONSOLE_MESSAGES constant using message parameters.
        ----------------------------------------------------------------------------------------------------------------
        """
        if system() == 'Windows':
            windll.kernel32.SetConsoleTextAttribute(windll.kernel32.GetStdHandle(-11),
                                                    self.COLORS[CONSOLE_MESSAGES[params[0]][0]])
        getattr(self._logger, CONSOLE_MESSAGES[params[0]][0].lower())(CONSOLE_MESSAGES[params[0]][1].
                                                                      format(*params[1:]))
        if system() == 'Windows':
            windll.kernel32.SetConsoleTextAttribute(windll.kernel32.GetStdHandle(-11), self.COLORS['DEFAULT'])
