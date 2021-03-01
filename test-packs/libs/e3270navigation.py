from taf.zos.py3270 import Display
from taf.zos.py3270 import keys

import libs.e3270utils as u


def cics_navigate_to_KCPRGNS(d: Display, timeout=30):
    d(key=keys.HOME)
    d('n.c', key=keys.ENTER, timeout=timeout)
    assert u.get_current_panel() == 'KCPSTART'

    u.zoom_into_first_row('CICSplex\nName', d=d)
    assert u.get_current_panel() == 'KCPRGNS'
