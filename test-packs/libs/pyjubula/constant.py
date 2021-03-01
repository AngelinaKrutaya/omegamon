"""
------------------------------------------------------------------------------------------------------------------------
    PyJubula :: constant.py
------------------------------------------------------------------------------------------------------------------------

    This module contains basic constants.

    (c) 2015 by the OXES QA Team

------------------------------------------------------------------------------------------------------------------------
"""

LOG_DEBUG \
    = 10
LOG_INFO \
    = 20
LOG_WARNING \
    = 30
LOG_ERROR \
    = 40

CONSOLE_MESSAGES = {
                    # -- Logger ----------------------------------------------------------------------------------------
                    "LOGGER_INVALID_LEVEL":
                        ("WARNING", "specified logging level is invalid, INFO level was applied"),
                    # -- Communicator ----------------------------------------------------------------------------------
                    "COMM_MESSAGE_SENDING":
                        ("DEBUG", "sending message '{}'"),
                    "COMM_MESSAGE_SENT":
                        ("DEBUG", "done"),
                    "COMM_MESSAGE_RECEIVING":
                        ("DEBUG", "receiving message"),
                    "COMM_MESSAGE_RECEIVED":
                        ("DEBUG", "done ({})"),
                    "COMM_INVALID_REPLY":
                        ("EXCEPTION", "invalid remote host reply"),
                    "COMM_NOT_CONNECTED":
                        ("EXCEPTION", "not connected"),
                    # -- AUT Agent -------------------------------------------------------------------------------------
                    "AGENT_CONNECTING":
                        ("INFO", "connecting to AUT agent on '{}:{}'"),
                    "AGENT_NO_HANDSHAKE":
                        ("EXCEPTION", "connection failed; check if the remote AUT agent is started"),
                    "AGENT_ANOTHER_CLIENT":
                        ("EXCEPTION", "connection failed; check if another client is connected"),
                    "AGENT_FAIL_UNKNOWN":
                        ("EXCEPTION", "connection failed for unknown reason"),
                    "AGENT_CONNECTED":
                        ("INFO", "connected"),
                    "AGENT_DISCONNECTED":
                        ("INFO", "disconnected"),
                    # -- Running AUT list request ----------------------------------------------------------------------
                    "AUT_LIST_ADD":
                        ("INFO", "requesting AUT list"),
                    "AUT_LIST_REMOVE":
                        ("INFO", "requesting AUT list"),
                    # -- Starting AUT ----------------------------------------------------------------------------------
                    "AUT_STARTING":
                        ("INFO", "starting '{}'"),
                    "AUT_ALREADY_STARTED":
                        ("WARNING", "the AUT is already started"),
                    "AUT_STARTING_REFUSED":
                        ("EXCEPTION", "the AUT starting request was refused: {}"),
                    "AUT_STARTED":
                        ("INFO", "the AUT has been started"),
                    # -- AUT stopping ----------------------------------------------------------------------------------
                    "AUT_STOPPING":
                        ("INFO", "stopping '{}'"),
                    "AUT_NOT_STARTED_WARN":
                        ("WARNING", "the AUT is not started"),
                    "AUT_STOPPED":
                        ("INFO", "the AUT has been stopped"),
                    # -- AUT connection --------------------------------------------------------------------------------
                    "AUT_CONNECTING":
                        ("INFO", "connecting to the AUT '{}'"),
                    "AUT_NOT_STARTED_ERR":
                        ("EXCEPTION", "the AUT is not started"),
                    "AUT_CONNECTED":
                        ("INFO", "connected"),
                    "AUT_DISCONNECTED":
                        ("INFO", "disconnected"),
                    "AUT_NO_PORT":
                        ("EXCEPTION", "unable to get port"),
                    "AUT_TIMEOUT":
                        ("EXCEPTION", "connection failed due to the timeout"),
                    # -- AUT definitions -------------------------------------------------------------------------------
                    "AUT_DEFINING":
                        ("INFO", "sending definitions to the AUT '{}'"),
                    "AUT_DEFINED":
                        ("INFO", "the AUT has been defined (threshold={}, name={}, hierarchy={}, context={})"),
                    # -- AUT screenshot --------------------------------------------------------------------------------
                    "AUT_SCREENSHOT":
                        ("INFO", "screenshot has been got"),
                    # -- AUT mapping -----------------------------------------------------------------------------------
                    "AUT_SWITCHING_MODE":
                        ("INFO", "switching the AUT mode"),
                    "AUT_SWITCHED_REGULAR":
                        ("INFO", "switched to regular mode"),
                    "AUT_SWITCHED_MAPPING":
                        ("INFO", "switched to mapping mode"),
                    "AUT_WRONG_MODE":
                        ("EXCEPTION", "the AUT is not in mapping mode"),
                    "AUT_MAPPING_RECEIVED":
                        ("INFO", "a mapping has been been received"),
                    # -- CAP proceeding --------------------------------------------------------------------------------
                    "CAP_REQUEST":
                        ("INFO", "requesting CAP (name='{}', type='{}', action='{}', params = '{}')"),
                    "CAP_SUCCESS":
                        ("INFO", "CAP has been applied (returned '{}')"),
                    "CAP_FAILED_ERR":
                        ("EXCEPTION", "CAP failed (code='{}', desc='{}')"),
                    "CAP_FAILED_WARN":
                        ("WARNING", "CAP failed (code='{}', desc='{}')"),
                    "CAP_CORRESPONDENCE":
                        ("INFO", "correspondence of found component is {} (name='{}', type='{}')"),
                    }
