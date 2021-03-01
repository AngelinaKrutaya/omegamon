"""
------------------------------------------------------------------------------------------------------------------------
    PyJubula :: __init__.py
------------------------------------------------------------------------------------------------------------------------

    PyJubula is an implementation of Jubula Functional Testing Tool API.
    It works with Python 3.
    NB! Only concrete and swing toolkits are implemented now.

    (c) 2015 by the OXES QA Team

------------------------------------------------------------------------------------------------------------------------
"""

from .communicator import config, AUT, AUTAgent, LOG_DEBUG, LOG_INFO, LOG_WARNING, LOG_ERROR
from .component import AppComponent, MenuBarComponent, TabbedComponent, TreeComponent, ButtonComponent, LabelComponent,\
    ListComponent, TextComponent, TableComponent, ComboBoxComponent

__author__ = "OXES QA Team"
__version__ = "0.6"
__all__ = ["config", "AUT", "AUTAgent",
           "AppComponent", "MenuBarComponent", "TabbedComponent", "TreeComponent", "ButtonComponent", "LabelComponent",
           "ListComponent", "TextComponent", "TableComponent", "ComboBoxComponent",
           "LOG_DEBUG", "LOG_INFO", "LOG_WARNING", "LOG_ERROR"
           ]
