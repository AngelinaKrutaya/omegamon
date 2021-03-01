"""
------------------------------------------------------------------------------------------------------------------------
    PyJubula :: component.py
------------------------------------------------------------------------------------------------------------------------

    This module contains Jubula AUT component implementation.
    It mirrors a native Jubula structure of AUT component classes.

    (c) 2015 by the OXES QA Team

------------------------------------------------------------------------------------------------------------------------
"""

from .communicator import CommunicatorError


class CAPError(CommunicatorError):
    """
    --------------------------------------------------------------------------------------------------------------------
    An exception type for AUTComponent class.
    Uses messages defined in the CONSOLE_MESSAGES constant.
    --------------------------------------------------------------------------------------------------------------------
    """

    pass


def not_critical(action):
    """
    --------------------------------------------------------------------------------------------------------------------
    A decorator to make a CAP request fail raise no exception, just return False.
    Doesn't change a global error handling mode.
    Use with methods of the _AUTComponent class and it's siblings.
    --------------------------------------------------------------------------------------------------------------------
    """
    def wrapped(*args):
        status = args[0]._aut.critical
        args[0]._aut.critical = False
        reply = action(*args)
        args[0]._aut.critical = status
        return reply
    return wrapped


class _AUTComponent:
    """
    --------------------------------------------------------------------------------------------------------------------
    AUT component base class.
    --------------------------------------------------------------------------------------------------------------------
    """

    def __init__(self, name, mapping, aut):
        """
        ----------------------------------------------------------------------------------------------------------------
        _AUTComponent Constructor.
        Args:
            name    (str):          logical name of component,
            params  (tuple):        component technical properties (type, name, hierarchy, context) for mapping,
            parent  (AUT object):   AUT instance reference bind to.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._aut = aut
        self._mapping = mapping
        self._name = name

    def execute(self, action, params):
        """
        ----------------------------------------------------------------------------------------------------------------
        Proceeds a CAP (component-action-parameter) action according to Jubula specification.
        Raises an exception if CAP fails and self._aut.critical is True.

        Args:
            action  (str):      string code of action,
            params  (tuple):    tuple of params.
        Returns:
            False if agent return code is not unity, otherwise str type reply of agent or just true.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._aut._logger.write("CAP_REQUEST", self._name, self.__class__.__name__, action, str(params))
        # If that's a AppComponent class then it is mapped by default
        default_mapping = 'true' if isinstance(self, AppComponent) else 'false'
        # Send a request
        self._aut._send_message(message_name="CAP",  message_type=2, definition=self._mapping,
                                action=action, params=params, default_mapping=default_mapping)
        reply = self._aut._get_response()
        # Return a reply due to the error handling mode
        while reply["state"] != "0":
            self._aut._logger.write("CAP_REQUEST", self._name, self.__class__.__name__, action, str(params))
            # If that's a AppComponent class then it is mapped by default
            default_mapping = 'true' if isinstance(self, AppComponent) else 'false'
            # Send a request
            self._aut._send_message(message_name="CAP", message_type=2, definition=self._mapping,
                                    action=action, params=params, default_mapping=default_mapping)
            reply = self._aut._get_response()
            #if reply["state"] != "0":
            #    if self._aut.critical:
            #        raise CAPError(["CAP_FAILED_ERR",], reply["error_code"], reply["error_desc"])
             #   else:
             #       self._aut._logger.write("CAP_FAILED_WARN", reply["error_code"], reply["error_desc"])
              #      return False
        result = reply["value"]
        self._aut._logger.write("CAP_SUCCESS", result)
        return result

    def recognize(self):
        """
        ----------------------------------------------------------------------------------------------------------------
        Checks a percentage of correspondence of the AUTComponent and real UI component.
        Args:
            none.
        Returns:
            (float): a percentage of correspondence.
        ----------------------------------------------------------------------------------------------------------------
        """
        default_mapping = 'true' if self.__class__.__name__ == 'AppComponent' else 'false'
        self._aut._send_message(message_name="CAP",  message_type=2, definition=self._mapping,
                                action="rcVerifyExists", params=(True, ), default_mapping=default_mapping)
        reply = float(self._aut._get_response()["match_percent"])
        self._aut._logger.write("CAP_CORRESPONDENCE", reply, self._name, self.__class__.__name__)
        return reply


class AppComponent(_AUTComponent):
    """
    --------------------------------------------------------------------------------------------------------------------
    Application component class.
    --------------------------------------------------------------------------------------------------------------------
    """
    
    """
    --------------------------------------------------------------------------------------------------------------------
    AUT component base class.
    --------------------------------------------------------------------------------------------------------------------
    """

    def __init__(self, name, aut, mapping=['', 'com.bredexsw.guidancer.autserver.swing.implclasses.GraphicApplication', [], []]):
        """
        ----------------------------------------------------------------------------------------------------------------
        _AUTComponent Constructor.
        Args:
            name    (str):          logical name of component,
            mapping (tuple):        component technical properties (type, name, hierarchy, context) for mapping,
            aut     (AUT object):   AUT instance reference bind to.
        ----------------------------------------------------------------------------------------------------------------
        """
        self._aut = aut
        self._mapping = mapping
        self._name = name
    
    def activate(self, method="AUT_DEFAULT"):
        return self.execute('rcActivate', (method,))

    def exists(self, title, operator="equals"):
        status = self._aut.critical
        self._aut.critical = False
        reply = self.execute('rcCheckExistenceOfWindow', (title, operator, True))
        self._aut.critical = status
        return reply

    def click(self, clicks=1, button=1, x=50, x_units='percent', y=50, y_units='percent'):
        return self.execute('rcClickDirect', (int(clicks), int(button), int(x), str(x_units), int(y), str(y_units)))

    def execute_command(self, command, rc=0, timeout=5000):
        return self.execute('rcExecuteExternalCommand', (command, rc, False, timeout))

    def input_text(self, text):
        return self.execute('rcNativeInputText', (text,))

    def send_keystroke(self, key, mod=''):
        return self.execute('rcNativeKeyStroke', (mod, key))

    def screenshot(self, file_name, delay=0, mode="overwrite", scale=100, create_dir=True):
        return self.execute('rcTakeScreenshot', (file_name, delay, mode, scale, create_dir))

    def screenshot_active(self, file_name, delay=0, mode="overwrite", scale=100, create_dir=True,
                          margin_top=0, margin_right=0, margin_bottom=0, margin_left=0):
        return self.execute('rcTakeScreenshotOfActiveWindow', (file_name, delay, mode, scale, create_dir,
                                                               margin_top, margin_right, margin_bottom, margin_left))

    def wait_for_window(self, title, operator="equals", timeout=1000, delay=200):
        return self.execute('rcWaitForWindow', (title, operator, timeout, delay))

    def wait_for_window_active(self, title, operator="equals", timeout=1000, delay=200):
        return self.execute('rcWaitForWindowActivation', (title, operator, timeout, delay))

    def wait_for_window_close(self, title, operator="equals", timeout=1000, delay=200):
        return self.execute('rcWaitForWindowToClose', (title, operator, timeout, delay))


class MenuBarComponent(AppComponent):
    """
    --------------------------------------------------------------------------------------------------------------------
    MenuBar component class.
    --------------------------------------------------------------------------------------------------------------------
    """

    def select_menu_item_by_index(self, path):
        return self.execute('selectMenuItemByIndexpath', (path,))
    
    def select_menu_item_by_text(self, path, operator):
        return self.execute('selectMenuItem', (path, operator))


class _GraphicsComponent(_AUTComponent):
    """
    --------------------------------------------------------------------------------------------------------------------
    Graphics component class.
    --------------------------------------------------------------------------------------------------------------------
    """

    def is_enabled(self):
        return self.execute('rcVerifyEnabled', (True,))

    def is_enabled_popup_by_index(self, path, button=3, x=None, x_units="percent", y=None, y_units="percent"):
        if x is None or y is None:
            return self.execute('rcPopupVerifyEnabledByIndexPath', (path, True, button))
        else:
            return self.execute('rcPopupVerifyEnabledByIndexPath', (x, x_units, y, y_units, path, True, button))

    def is_enabled_popup_by_text(self, path, operator="equals", button=3,
                                 x=None, x_units="percent", y=None, y_units="percent"):
        if x is None or y is None:
            return self.execute('rcPopupVerifyEnabledByTextPath', (path, operator, True, button))
        else:
            return self.execute('rcPopupVerifyEnabledByTextPath', (x, x_units, y, y_units,
                                                                   path, operator, True, button))

    @not_critical
    def exists(self):
        return self.execute('rcVerifyExists', (True,))

    def exists_popup_by_index(self, path, button=3, x=None, x_units="percent", y=None, y_units="percent"):
        if x is None or y is None:
            return self.execute('rcPopupVerifyExistsByIndexPath', (path, True, button))
        else:
            return self.execute('rcPopupVerifyExistsByIndexPath', (x, x_units, y, y_units, path, True, button))

    def exists_popup_by_text(self, path, operator="equals", button=3,
                             x=None, x_units="percent", y=None, y_units="percent"):
        if x is None or y is None:
            return self.execute('rcPopupVerifyExistsByTextPath', (path, operator, True, button))
        else:
            return self.execute('rcPopupVerifyExistsByTextPath', (x, x_units, y, y_units,
                                                                   path, operator, True, button))

    def has_focus(self):
        return self.execute('rcVerifyFocus',    (True,))

    def click(self, button=1, num=1, x=None, x_units="percent", y=None, y_units="percent"):
        if x is None or y is None:
            return self.execute('rcClick', (num, button))
        else:
            return self.execute('rcClickDirect', (num, button, x, x_units, y, y_units))

    def select_popup_by_index(self, path, button=3, x=None, x_units='percent', y=None, y_units='percent'):
        if not x or not y:
            params = (str(path), button)
        else:
            params = (x, x_units, y, y_units, str(path), button)
        return self.execute('rcPopupSelectByIndexPath', params)

    def select_popup_by_text(self, path, operator="equals", button=3,
                             x=None, x_units='percent', y=None, y_units='percent'):
        if not x or not y:
            params = (str(path), operator, button)
        else:
            params = (x, x_units, y, y_units, str(path), operator, button)
        return self.execute('rcPopupSelectByTextPath', params)

    def read_property(self, name):
        return self.execute('rcStorePropertyValue', ('dummy', name))

    def wait_for(self, timeout=1000, delay=200):
        return self.execute('rcWaitForComponent', (timeout, delay))


class TabbedComponent(_GraphicsComponent):
    """
    --------------------------------------------------------------------------------------------------------------------
    TabbedPane component class.
    --------------------------------------------------------------------------------------------------------------------
    """

    def is_enabled_tab_by_index(self, index):
        return self.execute('rcVerifyEnabledByIndex', (index, True))

    def is_enabled_tab_by_name(self, name, operator="equals"):
        return self.execute('rcVerifyEnabled', (name, operator, True))

    def exists_tab_by_name(self, name, operator="equals"):
        return self.execute('rcVerifyExistenceOfTab', (name, operator, True))

    def is_selected_tab_by_index(self, index):
        return self.execute('rcVerifySelectedTabByIndex', (index, True))

    def is_selected_tab_by_name(self, name, operator="equals"):
        return self.execute('rcVerifySelectedTab', (name, operator, True))

    def select_tab_by_index(self, index):
        return self.execute('rcSelectTabByIndex', (index,))

    def select_tab_by_name(self, name, operator='equals'):
        return self.execute('rcSelectTab', (name, operator))


class TreeComponent(_GraphicsComponent):
    """
    --------------------------------------------------------------------------------------------------------------------
    TreeComponent component class.
    --------------------------------------------------------------------------------------------------------------------
    """

    def exists_node_by_index(self, path, path_type="absolute", asc=0):
        return self.execute('rcVerifyPathByIndices', (path_type, asc, path, True))

    def exists_node_by_text(self, path, operator="equals", path_type="absolute", asc=0):
        return self.execute('rcVerifyPath', (path_type, asc, path, operator, True))

    def select_node_by_index(self, path, clicks=1, button=1, path_type="absolute", asc=0):
        return self.execute('rcSelectByIndices', (path_type, asc, path, clicks, button, "no"))

    def select_node_by_text(self, path, operator="equals", clicks=1, button=1, path_type="absolute", asc=0):
        return self.execute('rcSelect', (path_type, asc, path, operator, clicks, button, "no"))

    def selected_node(self):
        return self.execute('rcStoreSelectedNodeValue', ('dummy',))


class _ComponentWithText(_GraphicsComponent):
    """
    --------------------------------------------------------------------------------------------------------------------
    Component with text class.
    --------------------------------------------------------------------------------------------------------------------
    """

    pass


class ButtonComponent(_ComponentWithText):
    """
    --------------------------------------------------------------------------------------------------------------------
    Button component class.
    --------------------------------------------------------------------------------------------------------------------
    """

    pass


class LabelComponent(_ComponentWithText):
    """
    --------------------------------------------------------------------------------------------------------------------
    Label component class.
    --------------------------------------------------------------------------------------------------------------------
    """

    pass


class ListComponent(_ComponentWithText):
    """
    --------------------------------------------------------------------------------------------------------------------
    List component class.
    --------------------------------------------------------------------------------------------------------------------
    """

    def select_list_entry_by_index(self, index, extend_selection, button, num):
        return self.execute('rcSelectIndex', (index, extend_selection, button, num))
    
    def select_list_entry_by_text(self, text, operator, search_type, extend_selection, button, num):
        return self.execute('rcSelectValue', (text, operator, search_type, extend_selection, button, num))


class _ComponentWithTextInput(_ComponentWithText):
    """
    --------------------------------------------------------------------------------------------------------------------
    Component with text class.
    --------------------------------------------------------------------------------------------------------------------
    """

    pass


class TextComponent(_ComponentWithTextInput):
    """
    --------------------------------------------------------------------------------------------------------------------
    Text component class.
    --------------------------------------------------------------------------------------------------------------------
    """

    def text(self, text=None):
        if text is None:
            return self.execute('rcStorePropertyValue', ['dummy', 'text'])
        else:
            return self.execute('rcReplaceText', [text])


class TableComponent(_ComponentWithTextInput):
    """
    --------------------------------------------------------------------------------------------------------------------
    Table component class.
    --------------------------------------------------------------------------------------------------------------------
    """

    def exists_in_column(self, value, column, value_operator="equals", col_operator="equals", search_type="absolute", exists=False):
        return self.execute('rcVerifyValueInColumn', (column, col_operator, value, value_operator, search_type, exists))

    def exists_in_row(self, value, row, value_operator="equals", row_operator="equals", search_type="absolute", exists=False):
        return self.execute('rcVerifyValueInRow', (row, row_operator, value, value_operator, search_type, exists))


    def read_cell(self, x, y):
        return self.execute('rcReadValue', ['dummy', str(x), 'equals', str(y), 'equals'])

    def write_cell(self, x, y, text, col_rel='equals'):
        return self.execute('rcReplaceText', [text, str(x), 'equals', str(y), col_rel])

    def select_cell(self, row, column, button=1, col_rel='equals', clicks=1):
        return self.execute('rcSelectCell', [str(row), 'equals', str(column), col_rel, clicks, 50, 'percent', 50, 'percent',
                                             'no', button])

    def go_link(self, item):
        return self.execute('rcPopupSelectByTextPath', [item, 'equals', 3])

    def check_link(self, item):
        return self.execute('rcPopupVerifyExistsByTextPath', [item, 'equals', True, 3])

    def select_row(self, column, value):
        return self.execute('rcSelectRowByValue', [str(column), 'equals', str(value), 'equals', 1, 'no', 'absolute', 1])

    def select_next_row(self, column, value):
        return self.execute('rcSelectRowByValue', [str(column), 'equals', str(value), 'equals', 1, 'no', 'relative', 1])


class ComboBoxComponent(_ComponentWithTextInput):
    """
    --------------------------------------------------------------------------------------------------------------------
    Combo box component class.
    --------------------------------------------------------------------------------------------------------------------
    """

    def select_entry_by_text(self, item):
        return self.execute('rcSelectValue', (item+'.*', 'matches', 'absolute'))
    
    def select_entry_by_index(self, item):
        return self.execute('rcSelectIndex', [str(item)])

    def text(self, text=None):
        if text is None:
            return self.execute('rcStorePropertyValue', ['dummy', 'selectedItem'])
        else:
            return self.execute('rcReplaceText', [text])
