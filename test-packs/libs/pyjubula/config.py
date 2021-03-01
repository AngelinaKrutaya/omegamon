"""
------------------------------------------------------------------------------------------------------------------------
    PyJubula :: config.py
------------------------------------------------------------------------------------------------------------------------

    This module contains a configuration.

    (c) 2015 by the OXES QA Team

------------------------------------------------------------------------------------------------------------------------
"""

from os.path import dirname

TCP_TIMEOUT \
    = 5
TCP_BUFFER \
    = 1024
LOG_LEVEL \
    = 20
AGENT_IP_DEFAULT \
    = 'localhost'
AGENT_PORT_DEFAULT \
    = 60000
AUT_LOCALE_DEFAULT \
    = "en_US"
AGENT_TIMEOUT \
    = 10
AUT_PORT_DEFAULT \
    = 52414
AUT_LISTEN_TIMEOUT \
    = 10
XML_PATH \
    = dirname(__file__)+'/xml/'
