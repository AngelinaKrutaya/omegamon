"""
Example:
import libs.e3270utils as u

then set display before first use:

u.display = display

"""

import logging
import re
from taf.zos.py3270 import keys
from taf.zos.py3270 import Emulator
from taf.zos.py3270.display import Display
from typing import Tuple
from taf.af_support_tools import TAFConfig

root = TAFConfig().testpack_root

logger = logging.getLogger(__name__)

display = None


# def navigate_to_start():
#     display(key=keys.HOME, timeout=5)
#     display('N.D', key=keys.ENTER, timeout=30)

def tab(timeout: int = 10):
    global display
    return display('', key=keys.TAB, timeout=timeout)


def click_tab(tab, d: Display = None):
    if d is None:
        global display
    else:
        display = d
    display.find(tab)('', keys.ENTER, 30)


def zoom_in(line, action, d: Display = None):
    if d is None:
        global display
    else:
        display = d
    logger.info(f"Zooming into line {line} with action {action}")
    while display.find(line) is None:
        display('', keys.PF8, 10)
    display.find(line).shift((0, -2))(action, keys.ENTER, 30)


def zoom_in_regex(line, action):
    display.find(regex=line).shift((0, -2))(action, keys.ENTER, 30)


def get_current_panel(d: Display = None):
    if d is None:
        global display
    else:
        display = d
    return str(display[3, 1:9]).strip()


def back_to_ZMENU():
    global display
    while get_current_panel() not in ('KOBSEVTS', 'KOBSZOS', 'KOBSCICS', 'KOBSCTG', 'KOBSIMS', 'KOBSDB2', 'KOBSMQ',
                                      'KOBSMFN', 'KOBSSTOR', 'KOBSJVM'):
        display('', key=keys.PF3, timeout=30)
        if display.find('Exit and terminate the session'):
            display('', key=keys.PF3, timeout=30)
            break
        if display.find('===> Enter: LOGON'):
            break
    display(key=keys.HOME)


def find_and_press_button(button_text: str):
    """
    button is usually located on the very bottom line of the panel.
    So to find the button we need to find the last line of the workspace first.
    The function is not tested for all the buttons available. So it may need adjustments.
    :param button_text:
    :return:
    """
    corners_regex = (r' в”Њ', r'в”ђ $', r'в” $', r'\n в””')
    areas = display.find_all_by_frame(corners_regex=corners_regex)
    if not areas:
        area = display[1:-1, :]
    else:
        area = areas[-1][1:-1, :]
    last_line = area[-1, :]
    logger.info(f"Last line: {last_line}")
    n = len(area.rows) - 2
    while n > 0:
        if last_line.strip('в”‚ ') == '' or last_line.strip('в”‚ ').startswith('Note'):
            last_line = area[n - len(area.rows), :]
            n -= 1
        else:
            break
    if len(last_line.fields) >= 3:
        for f in last_line.fields:
            if 'REVERSE' in f.highlighting:
                logger.info(f'Button found: {str(f)}')
                if str(f).strip() == button_text:
                    logger.info(f"Pressing button {button_text}...")
                    f('', keys.ENTER, 30)
                    return True
    return False


def get_text_position(text, rg=False, d: Display = None):
    """
    Return text position.
    :param d: display
    :param text:
    :param rg: regex or not
    :return: (y, x)
    """
    if d is None:
        global display
    else:
        display = d
    res = (None, None)
    if rg:
        exp_match = display.find(regex=text)
    else:
        exp_match = display.find(text)
    if exp_match is not None:
        y1, x1 = exp_match.x
        res = (y1, x1)
    return res


def zoom_into_first_row(column, zoom='s',  d: Display = None):
    if d is None:
        global display
    else:
        display = d
    y, x = get_text_position(column)
    res = str(display[y + 3, 5:13])
    zoom_in(res, zoom)
    return res


def logon_beacon(host: str, applid: str, username: str, password: str, oversize: Tuple[int, int] = (62, 160)):
    emulator = Emulator(host, model=2, oversize=oversize)
    welcome = emulator.display.find('===> Ex.: LOGON <userid>, TSO <userid>')
    if welcome:
        logger.info(f"Logging to E3270UI applid {applid}")
        welcome.shift((1, 0))(f'L {applid}', keys.ENTER, 30)
    emulator.display(username, keys.TAB, 10)
    emulator.display(password, keys.ENTER, 100)
    if emulator.display.find("OMEGAMON e3270UI What's New"):
        emulator.display(key=keys.PF3)
    return emulator


def close_beacon(emulator: Emulator):
    logger.info("exiting applid")
    try:
        emulator.display(key=keys.HOME)
        emulator.display('=x', key=keys.ENTER, timeout=1000)
    finally:
        emulator.disconnect()
        emulator.close()
        logger.info("emulator was closed successfully")


def get_column_yx(column, d: Display = None):
    if d is None:
        global display
    else:
        display = d
    y, x = None, None
    y, x = get_text_position(column, d=display)
    # probably column is not on first screen, need to scroll to the right
    if y is None:
        max_num = 8
        num = 0
        while y is None and num < max_num:
            num = num + 1
            display(key=keys.HOME, timeout=5)
            display('', key=keys.PF11, timeout=30)
            y, x = get_text_position(column, d=display)
    return (y, x)


def get_cursor_on_first_row_in_column(column, width=8, number_cell=1, d: Display = None):
    if d is None:
        global display
    else:
        display = d
    y, x = get_column_yx(column, d=display)
    step = 1
    for i in range(0, number_cell):
        type_column = str(display[y + step:y + step + 1, x:x + width])
        while '───' not in type_column:
            step += 1
            type_column = str(display[y + step:y + step + 1, x:x + width])
        step += 1
    return (y + step, x)


def get_column_list(column, width=8, d: Display = None):
    if d is None:
        global display
    else:
        display = d
    l = []
    y, x = get_column_yx(column, d=display)
    if str(display[y + 3: y + 4, x: x + 1]) == ' ':
        type_column = str(display[y + 3:, x + 2:x + 2 + width])
    else:
        type_column = str(display[y + 3:, x:x + width])
    type_column_list = type_column.split('\n')
    for el in type_column_list:
        if '───' in el:
            break
        else:
            l.append(el.strip())
    return l


def shift_cursor(direction='right', pos=1):
    if direction == 'right':
        display.cursor = display.cursor[0], display.cursor[1] + pos
    elif direction == 'left':
        display.cursor = display.cursor[0], display.cursor[1] - pos
    elif direction == 'top':
        display.cursor = display.cursor[0] - pos, display.cursor[1]
    elif direction == 'bottom':
        display.cursor = display.cursor[0] + pos, display.cursor[1]


def get_date_time_from_screen(d: Display = None):
    """
    :param d: Display
    :return: date, time
    """
    if d is None:
        global display
    else:
        display = d
    row_with_date = str(display[0, :])
    m = re.match(r'.* (?P<cur_date>[0-9]{2}/[0-9]{2}/[0-9]{4}) (?P<cur_time>[0-9]{2}:[0-9]{2}:[0-9]{2}).*',
                 row_with_date)
    return m.group('cur_date'), m.group('cur_time')
