"""
------------------------------------------------------------------------------------------------------------------------
    PyJubula :: communicator.py
------------------------------------------------------------------------------------------------------------------------

    This module contains net layer implementation.

    (c) 2015 by the OXES QA Team

------------------------------------------------------------------------------------------------------------------------
"""

import socket
import select
import re
import xml.etree.ElementTree as et
from jinja2 import Template
from time import time
from base64 import b64decode
from xml.sax.saxutils import escape

from .logger import Logger
from .config import *
from .constant import *


def config(tcp_timeout=TCP_TIMEOUT,
           tcp_buffer=TCP_BUFFER,
           log_level=LOG_LEVEL,
           agent_ip_default=AGENT_IP_DEFAULT,
           agent_port_default=AGENT_PORT_DEFAULT,
           aut_port_default=AUT_PORT_DEFAULT,
           aut_listen_timeout=AUT_LISTEN_TIMEOUT,
           aut_locale_default=AUT_LOCALE_DEFAULT,
           xml_path=XML_PATH):
    """
    --------------------------------------------------------------------------------------------------------------------
    Allow to change the module configuration.
    --------------------------------------------------------------------------------------------------------------------
    """
    global TCP_TIMEOUT, TCP_BUFFER, LOG_LEVEL, AGENT_IP_DEFAULT, AGENT_PORT_DEFAULT, AUT_PORT_DEFAULT, \
        AUT_LISTEN_TIMEOUT, AUT_LOCALE_DEFAULT, XML_PATH
    TCP_TIMEOUT = tcp_timeout
    TCP_BUFFER = tcp_buffer
    LOG_LEVEL = log_level
    AGENT_IP_DEFAULT = agent_ip_default
    AGENT_PORT_DEFAULT = agent_port_default
    AUT_PORT_DEFAULT = aut_port_default
    AUT_LISTEN_TIMEOUT = aut_listen_timeout
    AUT_LOCALE_DEFAULT = aut_locale_default
    XML_PATH = xml_path


class CommunicatorError(Exception):
    """
    --------------------------------------------------------------------------------------------------------------------
    An exception type for Communicator class.
    Uses messages defined in the CONSOLE_MESSAGES constant.
    --------------------------------------------------------------------------------------------------------------------
    """

    def __init__(self, *params):
        """
        ----------------------------------------------------------------------------------------------------------------
        Initialize an exception using the CONSOLE_MESSAGES constant for it's message.
        Args:
            params    (list):    message parameters.
        ----------------------------------------------------------------------------------------------------------------
        """
        if len(params) > 1:
            super().__init__(CONSOLE_MESSAGES[params[0]][1].format(*params[1:]))
        else:
            super().__init__(CONSOLE_MESSAGES[params[0]][1])


class AUTAgentError(CommunicatorError):
    """
    --------------------------------------------------------------------------------------------------------------------
    An exception type for AUTAgent class.
    --------------------------------------------------------------------------------------------------------------------
    """

    pass


class AUTError(CommunicatorError):
    """
    --------------------------------------------------------------------------------------------------------------------
    An exception type for AUT class.
    --------------------------------------------------------------------------------------------------------------------
    """

    pass


class _Communicator:
    """
    --------------------------------------------------------------------------------------------------------------------
    Process data exchange via TCP/IP.
    Used for AUTAgent and AUT classes.
    --------------------------------------------------------------------------------------------------------------------
    """

    def __init__(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        Communicator constructor.
        Initializes logging, message numeration and opens a TCP socket.
        Args:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        # Initialize logging
        self._logger = Logger(self.__class__.__name__, LOG_LEVEL)
        # Initialize TCP socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Initialize message numerator
        self._message_num = 0

    def _read(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        Reads binary data from self._socket.
        Args:
            none.
        Returns:
            bytes object read from self._socket.
        ----------------------------------------------------------------------------------------------------------------
        """
        data = b''
        ready = select.select([self._socket], [], [], TCP_TIMEOUT)
        if ready[0]:
            data = self._socket.recv(TCP_BUFFER)
        return data

    def _write(self, data):
        """
        ----------------------------------------------------------------------------------------------------------------
        Writes binary data into self._socket.
        Args
            data (bytes object).
        Returns:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        ready = select.select([], [self._socket], [], TCP_TIMEOUT)
        if ready[1]:
            self._socket.sendall(data)
        else:
            raise CommunicatorError("COMM_NOT_CONNECTED")

    def _send_message(self, message_name, message_type, **message_params):
        """
        ----------------------------------------------------------------------------------------------------------------
        Sends message to AUTAgent or AUT.
        Args:
            message_name   (str):   message name,
            message_type   (int):   Jubula message type code,
            message_params (dict):  message specific parameters (look [XML_PATH+message_name].xml for details).
        Returns:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._logger.write("COMM_MESSAGE_SENDING", message_name)
        # Make message body
        body = Template(open(XML_PATH+message_name+'.xml').read())
        body = body.render(type=type, str=str, escape=escape,
                           message_number=self._message_num+1,
                           message_timestamp=int(time()*1000),
                           **message_params)
        # Make message header
        header = Template(open(XML_PATH+'Header.xml').read())
        header = header.render(message_type=message_type,
                               message_class=re.findall('^<[a-zA-Z0-9\.]+>', body)[0][1:-1],
                               message_length=len(body))
        # Send message
        self._write(bytes(('#' + str(len(header)) + '\n' + header + body).encode('ascii')))
        self._message_num += 1
        self._logger.write("COMM_MESSAGE_SENT")

    def _receive_message(self, expected_name=None):
        """
        ----------------------------------------------------------------------------------------------------------------
        Receives message objects from AUTAgent or AUT.
        Args:
            expected_name    (str): expected message name.
        Returns:
            message specific dict.
        ----------------------------------------------------------------------------------------------------------------
        """
        def get_value(target, path, is_list=False, result=None):
            """
            ------------------------------------------------------------------------------------------------------------
            Searches specified in path values recursively. Returns a list if "is_list" is True.
            Args:
                target   (XML element):  XML object to search values in,
                path     (tuple):        tuple comprised of element hierarchy (not necessary full),
                is_list  (bool):         True if expected result is a list,
                result   (None):         variable to save result in.
            Returns:
                message specific dict.
            ------------------------------------------------------------------------------------------------------------
            """
            # Initialize result variable if this is the first recursive step
            if target is body:
                result = []
            # Start search using the path
            for x in target.iter(path[0]):
                if len(path) == 1:
                    result.append(str(x.text) if x.text is not None else "")
                else:
                    get_value(x, path[1:], is_list, result)
            # Return result
            if target == body:
                if is_list:
                    return result
                elif len(result) > 0:
                    return result[0]

        self._logger.write("COMM_MESSAGE_RECEIVING")
        # Wait for data received can be parsed properly
        data = b''
        while True:
            try:
                data += self._read()
                tmp = re.findall('(?<=^#)[^\\n]+|'
                                 '\\<[\\w\\.]+MessageHeader\\>[\\W\\w]*\\</[\\w\\.]+MessageHeader\\>'
                                 '|(?<=\\<\\?xml version="1.0" minor="1" major="1"\\?\\>)[\\W\\w]+$',
                                 data.decode('utf-8'))
                et.fromstring(tmp[1])
                body = et.fromstring(tmp[2])
                break
            except IndexError:
                pass
            except et.ParseError:
                pass
        # Check some length conditions
        if int(tmp[0]) != len(tmp[1]):
            raise CommunicatorError("COMM_INVALID_REPLY")
        # Read common message properties
        reply = {"mess_name": body.tag.split('.')[-1],
                 "bind_id": get_value(body, ("m__bindId", "m__sequenceNumber")),
                 }
        # Check if received message is an expected one
        if expected_name is not None and expected_name != reply["mess_name"]:
            raise CommunicatorError("COMM_INVALID_REPLY")
        # Read message specific properties
        if reply["mess_name"] == "StartAUTServerStateMessage":
            reply["reason"] = get_value(body, ("m__reason",))
            reply["description"] = get_value(body, ("m__description",))
        elif reply["mess_name"] == "AutRegisteredMessage":
            reply["aut_id"] = get_value(body, ("m__autId", "m__executableName"))
            reply["registered"] = get_value(body, ("m__registered",))
        elif reply["mess_name"] == "RegisteredAutListMessage":
            reply["aut_ids"] = get_value(body, ("m__autIds", "m__executableName"), True)
        elif reply["mess_name"] == "TakeScreenshotResponseMessage":
            reply["screenshot"] = get_value(body, ("m__screenshot", "m__data"))
        elif reply["mess_name"] == "CAPTestResponseMessage":
            reply["state"] = get_value(body, ("m__state",))
            reply["value"] = get_value(body, ("m__returnValue",))
            reply["error_code"] = get_value(body, ("m__testErrorEvent", "m__id"))
            try:
                desc = get_value(body, ("m__testErrorEvent", "m__properties", "string"), True)[1]
            except IndexError:
                desc = ''
            reply["error_desc"] = desc
            reply["match_percent"] = get_value(body, ("m__messageCap", "m__ci", "m__matchPercentage"))
        elif reply["mess_name"] == "ObjectMappedMessage":
            reply["supported_type"] = get_value(body, ("m__componentIdentifiers", "m__supportedClassName"))
            reply["technical_type"] = get_value(body, ("m__componentIdentifiers", "m__componentClassName"))
            reply["hierarchy"] = get_value(body, ("m__componentIdentifiers", "m__hierarchyNames", "string"), True)
            reply["neighbours"] = get_value(body, ("m__componentIdentifiers", "m__neighbours", "string"), True)
        elif reply["mess_name"] == "AUTModeChangedMessage":
            reply["mode"] = get_value(body, ("m__mode",))
        self._logger.write("COMM_MESSAGE_RECEIVED", str(reply))
        return reply

    def _get_response(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        Wait for response for the last sent request using message numerator.
        Args:
            none.
        Returns:
            response (dict).
        ----------------------------------------------------------------------------------------------------------------
        """
        response = self._receive_message()
        if response["bind_id"] != str(self._message_num):
            raise CommunicatorError("COMM_INVALID_REPLY")
        return response


class AUTAgent(_Communicator):
    """
    --------------------------------------------------------------------------------------------------------------------
    Process data exchange with AUT agent via TCP/IP.
    --------------------------------------------------------------------------------------------------------------------
    """
    def __init__(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        AUTAgent constructor.
        Args:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        super().__init__()
        # Initialize running AUTs list
        self._tcp_host = None
        self._tcp_port = None
        self.aut_list = []

    def _receive_message(self, expected_name=None):
        """
        ----------------------------------------------------------------------------------------------------------------
        Add default proceeding of registration messages (it can be sent by agent with no request).
        Args:
            expected_name   (str):  an expected message name.
        Returns:
            message specific dict.
        ----------------------------------------------------------------------------------------------------------------
        """
        reply = super()._receive_message()
        # Check if the message is a registration stuff and act respectively
        if reply["mess_name"] == "AutRegisteredMessage":
            if reply["registered"] == "true":
                self.aut_list.append(reply["aut_id"])
            elif reply["registered"] == "false":
                self.aut_list.remove(reply["aut_id"])
            else:
                raise CommunicatorError("COMM_INVALID_REPLY")
        # Check if received message is an expected one and if it's a registration one, wait the next message
        if expected_name is not None and expected_name != reply["mess_name"]:
            if reply["mess_name"] == "AutRegisteredMessage":
                reply = self._receive_message(expected_name)
            else:
                raise CommunicatorError("COMM_INVALID_REPLY")
        return reply

    def connect(self, host=AGENT_IP_DEFAULT):
        """
        ----------------------------------------------------------------------------------------------------------------
        Initialize a connection with AUT agent.
        Args:
            host (str):   AUT agent host in "host[:port]" format.
        Returns:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        # Parse AUTAgent target host settings
        if ':' in host:
            self._tcp_host, self._tcp_port = host.split(':')
        else:
            self._tcp_host, self._tcp_port = host, AGENT_PORT_DEFAULT
        self._tcp_port = int(self._tcp_port)
        self._logger.write("AGENT_CONNECTING", self._tcp_host, self._tcp_port)
        self._socket.connect((self._tcp_host, self._tcp_port))
        # Jubula's handshake
        request = self._read()
        if request != b"ClientTypeRequest/11\r\n" and request+self._read() != b"ClientTypeRequest/11\r\n":
            raise AUTAgentError("AGENT_NO_HANDSHAKE")
        self._write(b"ClientType.Exclusive\r\n")
        data = self._read()+self._read()
        if data == b"0/11\r\n":
            pass
        elif data == b"1/11\r\n":
            raise AUTAgentError("AGENT_ANOTHER_CLIENT")
        else:
            raise AUTAgentError("AGENT_FAIL_UNKNOWN")
        # Init aut list
        self._send_message('GetAUTList', 3)
        self.aut_list = self._get_response()["aut_ids"]
        # Some additional requests
        self._send_message("CompSystem", 2)
        self._logger.write("AGENT_CONNECTED")

    def disconnect(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        Close the connection with AUT agent.
        Args:
            none.
        Returns:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._send_message(message_name="DisconnectFromAgent", message_type=2)
        self._get_response()
        self._socket.close()
        self._logger.write("AGENT_DISCONNECTED")

    def start_aut(self, aut_id, jre_params, aut_params, jre_binary, class_path, class_name, working_dir,
                  locale=AUT_LOCALE_DEFAULT):
        """
        ----------------------------------------------------------------------------------------------------------------
        Send a request to AUT agent to start an AUT and wait the AUT registration with the agent.
        Args:
            aut_id      (str): AUT id,
            jre_params  (str): JRE parameters,
            aut_params  (str): AUT command line parameters
            jre_binary  (str): JRE executable full path,
            class_path  (str): jar files to execute (delimiter is ";"),
            class_name  (str): entry point,
            working_dir (str): AUT working dir on the remote host,
            locale      (str): AUT locale.
        Returns:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._logger.write("AUT_STARTING", aut_id)
        if aut_id in self.aut_list:
            self._logger.write("AUT_ALREADY_STARTED")
            return
        self._send_message(message_name="StartAUT", message_type=2, agent_host=self._tcp_host,
                           agent_port=self._tcp_port, aut_id=aut_id, locale=locale, jre_params=jre_params,
                           aut_params=aut_params, jre_binary=jre_binary, class_path=class_path, class_name=class_name,
                           working_dir=working_dir)
        response = self._get_response()
        if response["reason"] != "0":
            raise AUTAgentError("AUT_STARTING_REFUSED", response["description"])
        # Wait for the AUT be registered by agent
        self._receive_message("AutRegisteredMessage")
        self._logger.write("AUT_STARTED")

    def stop_aut(self, aut_id):
        """
        ----------------------------------------------------------------------------------------------------------------
        Send a request to stop an AUT and wait the AUT registration with the agent.
        Args:
            aut_id (str): an AUT id to be stopped.
        Returns:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._logger.write("AUT_STOPPING", aut_id)
        if aut_id not in self.aut_list:
            self._logger.write("AUT_NOT_STARTED_WARN")
            return
        self._send_message(message_name="StopAUT", message_type=2, aut_id=aut_id)
#        self._receive_message("AutRegisteredMessage")
#        self._get_response()
#        self._logger.write("AUT_STOPPED")

    def aut_connect(self, aut_id):
        """
        ----------------------------------------------------------------------------------------------------------------
        Connect to running AUT using specified AUT id.
        Args:
            aut_id (str): an AUT id to be connected to.
        Returns:
            AUT object.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._logger.write("AUT_CONNECTING", aut_id)
        if aut_id not in self.aut_list:
            raise AUTError("AUT_NOT_STARTED_ERR")
        aut = AUT(aut_id)
        self._send_message(message_name='ConnectToAUT', message_type=2, client_host=socket.gethostname(),
                           client_port=aut._tcp_port, aut_id=aut_id)
        self._get_response()
        aut._connect()
        self._logger.write("AUT_CONNECTED", aut_id)
        return aut


class AUT(_Communicator):
    """
    --------------------------------------------------------------------------------------------------------------------
    Process data exchange with AUT via TCP/IP.
    --------------------------------------------------------------------------------------------------------------------
    """
    def __init__(self, aut_id):
        """
        ----------------------------------------------------------------------------------------------------------------
        AUT constructor.
        Args:
            aut_id (str):   AUT id to work with.
        ----------------------------------------------------------------------------------------------------------------
        """
        super().__init__()
        # Set up AUTId and CAP error handling mode (if critical then raise an exception when CAP fails)
        self.aut_id = aut_id
        self.critical = True
        # Enable listener net settings
        self._listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_port = AUT_PORT_DEFAULT
        while True:
            try:
                self._listener.bind(('', self._tcp_port))
                break
            except OSError:
                if self._tcp_port >= 60000:
                    raise AUTError("AUT_NO_PORT")
                self._tcp_port += 1
                continue
        # Set mapping mode flag
        self.mapping_mode = False

    def _connect(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        Initialize a connection with an AUT. A request for AUT agent should be sent before!
        Args:
            none.
        Returns:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._listener.listen(1)
        self._listener.settimeout(AUT_LISTEN_TIMEOUT)
        try:
            self._socket = self._listener.accept()[0]
        except socket.timeout:
            raise AUTError("AUT_TIMEOUT")
        # Jubula's handshake
        self._write(b'ClientTypeRequest/11\r\n')
        reply = self._read()
        if reply != b'ClientType.Exclusive\r\n' and reply+self._read() != b'ClientType.Exclusive\r\n':
            raise CommunicatorError('connection failed')
        self._write(b'0/11\r\n')
        # Some additional requests
        self._send_message(message_name='GetKeyboardLayout', message_type=3)
        self._get_response()
        self._send_message(message_name='CompSystem', message_type=2)

    def disconnect(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        Close the connection with the AUT.
        Args:
            none.
        Returns:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._listener.close()
        self._socket.close()
        self._logger.write("AUT_DISCONNECTED")

    def define(self, threshold=1.0, name_factor=1.0, path_factor=0.7, context_factor=0.0):
        """
        ----------------------------------------------------------------------------------------------------------------
        Send definitions to the AUT.
        Args:
            threshold       (float):    map threshold,
            name_factor     (float):    map name weight,
            path_factor     (float):    map path weight,
            context_factor  (float):    map context weight.
        Returns:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._logger.write("AUT_DEFINING", self.aut_id)
        self._send_message(message_name='Supported', message_type=2, threshold=threshold,
                           name_factor=name_factor, path_factor=path_factor, context_factor=context_factor)
        self._get_response()
        self._logger.write("AUT_DEFINED", threshold, name_factor, path_factor, context_factor)

    def screenshot(self, file_name=None):
        """
        ----------------------------------------------------------------------------------------------------------------
        Takes a screenshot of remote string. Saves it to local file if file name is specified.
        Returns the image byte stream.
        NB! A screenshot method of ApplicationComponent class can save screenshot only on the agent host.

        Args:
            file_name (str):  file name.
        Returns:
            byte array of the image.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._send_message(message_name="TakeScreenshot", message_type=3)
        image = b64decode(self._get_response()["screenshot"])
        if file_name:
            open(file_name, "wb").write(image)
        self._logger.write("AUT_SCREENSHOT")
        return image

    def toggle_mode(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        Toggles the AUT mode (mapping mode / regular testing mode).
        Args:
            none.
        Returns:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._logger.write("AUT_SWITCHING_MODE")
        if self.mapping_mode:
            (mode, key_modifier, key, mouse_button) = (1, 0, 0, 0)
        else:
            (mode, key_modifier, key, mouse_button) = (2, 192, 81, -1)
        self._send_message(message_name="MappingMode", message_type=2, mode=mode, key_modifier=key_modifier, key=key,
                           mouse_button=mouse_button)
        self._get_response()
        # For unknown reason agent tells us about switching to normal mode twice
        if self.mapping_mode:
            self._receive_message("AUTModeChangedMessage")
            self._logger.write("AUT_SWITCHED_REGULAR")
        else:
            self._logger.write("AUT_SWITCHED_MAPPING")
        self.mapping_mode = not self.mapping_mode

    def set_mapping_mode(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        Set mapping AUT mode.
        Args:
            none.
        Returns:
            none.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._logger.write("AUT_SWITCHING_MODE")
        if self.mapping_mode:
            return
        else:
            (mode, key_modifier, key, mouse_button) = (2, 192, 81, -1)
        self._send_message(message_name="MappingMode", message_type=2, mode=mode, key_modifier=key_modifier, key=key,
                           mouse_button=mouse_button)
        self._get_response()
        self.mapping_mode = True


    def get_mapping(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        Receives a mapping of component pointed by user using CTRL+SHIFT+q keystroke (like in Jubula ITE).
        Args:
            none.
        Returns:
            list of component technical definitions.
        ----------------------------------------------------------------------------------------------------------------
        """
        if not self.mapping_mode:
            raise AUTError("AUT_WRONG_MODE")
        mapping = self._receive_message("ObjectMappedMessage")
        self._logger.write("AUT_MAPPING_RECEIVED")
        return [mapping["supported_type"], mapping["technical_type"], mapping["hierarchy"], mapping["neighbours"]]
