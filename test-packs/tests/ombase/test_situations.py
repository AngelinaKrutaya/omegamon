import pytest
import random
from taf import logging
from taf.zos.jes import JESAdapter
from taf.zos.py3270 import keys
from taf.zos.py3270 import BlueZone

import libs.e3270utils as u
from libs.ite1db2 import *
from libs.creds import *
from libs.ivtenv import rtes
import time

rte = os.environ.get('rte', 'ite1')
hostname = rtes[rte]['hostname']
applid = rtes[rte]['tom_applid']

username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# root = TAFConfig().testpack_root

SIT_NAME = f'Test_Sit{random.randint(1, 9999):04d}'
WAIT_JOB = f'IVT{random.randint(1, 99999):05d}'


@pytest.fixture(scope='function')
def bluezone():
    bz = BlueZone(target=hostname, model=2)
    display = bz.display()
    display('MX ' + username).enter()
    display.wait(10, 'ENTER PASSWORD')
    display(password).enter()
    display.wait(10, 'Enter LOGON parameters below:')
    display.enter()
    display.wait(10, '***')
    display.enter()
    display.wait(10, 'ISPF Primary Option Menu')
    yield display
    bz.close()


def create_sit(d, sit_name, om, table, column, distribution, value):
    d(key=keys.HOME)
    d('e.s', key=keys.ENTER)
    u.zoom_in(om, '')
    assert d.find('Create New Situation')
    # should be fast enough
    d(sit_name, key=keys.ENTER, timeout=5)
    assert d.find('KOBSEDPD')
    while not d.find(table):
        d.find('Table Name')('', key=keys.PF8)
    u.zoom_in(table, 'S')
    while not d.find(column):
        d.find('Column Name')('', key=keys.PF8)
    u.zoom_in(column, 'S')
    assert d.find(regex=f' {column} .* Yes      ')
    u.click_tab(' Accept ')
    assert d.find('KOBSEDTF')
    u.zoom_in('Interval', 'S')
    assert d.find('KOBSEDEF')
    u.tab()
    # set 30 seconds
    d('00')
    u.tab()
    d('00')
    u.tab()
    d('30').enter()
    u.zoom_in('*IF *VALUE', 'S')
    assert d.find('KOBSEDPA')
    u.zoom_in('VALUE == 0', 'S')
    assert d.find('Options Menu')
    d('1').enter()
    d.find(table.replace(' ', '_')).shift((1, 2))(f'{value}').enter()
    u.click_tab(' Accept ')
    u.click_tab(' Accept ')
    assert u.get_current_panel() == 'KOBSEDTF'
    u.click_tab(' Distribution ')
    assert u.get_current_panel() == 'KOBSEDTD'
    u.zoom_in(distribution, 'S')
    # check that system has been added
    assert d.find(regex='Systems                    .*Overrides').shift((2, 0)).find(distribution)
    u.click_tab(' Formula ')
    assert u.get_current_panel() == 'KOBSEDTF'
    u.click_tab(' OK ')
    return True


def find_sit(d, sit_name, om):
    d(key=keys.HOME)
    d('e.s', key=keys.ENTER)
    d.find(regex=f'\+ .* {om}')('', key=keys.ENTER)

    y1, _ = d.find(regex=f'\- .* {om}').x
    cur_line = 'xxxxxx'
    while cur_line != str(d[y1 + 1, :]) and not d.find(sit_name):
        cur_line = str(d[y1 + 1, :])
        d('', key=keys.PF8)
    return True if d.find(sit_name) else False


def switch_hub(d, hub_name):
    max_hub_chars = 16
    d.find('«')('', key=keys.ENTER)
    # we have word 'Hub' several times
    d.find(regex='RTE.*NAV').shift((0, -4))('', key=keys.ENTER)
    # we have word 'next' several times
    d.find(regex='CANCEL   NEXT').shift((0, 10))('', key=keys.ENTER)
    if len(hub_name) <= max_hub_chars:
        u.zoom_in(hub_name, 'S')
    else:
        table_y, _ = d.find('Hub Name   ').x
        end_y, _ = d.find(regex='BACK.*HOME').x
        areas1 = [area.x[0] for area in d.find_all(hub_name[0:max_hub_chars]) if table_y < area.x[0] < end_y]
        d.find('Hub Name   ')('', key=keys.PF11)
        areas2 = [area.x[0] for area in d.find_all(hub_name[max_hub_chars:] + ' ') if table_y < area.x[0] < end_y]
        y = list(set(areas1).intersection(areas2))[0]
        d.cursor = y, 3
        d('S', key=keys.ENTER)
    d('1', key=keys.ENTER)
    d.find('OK   SAVE').shift((0, 6))('', key=keys.ENTER)
    return True if d.find('Hub ' + hub_name) else False


def test_create_sit(e3270_in_out):
    create_sit(e3270_in_out, SIT_NAME, 'MVS System', 'Address Space CPU Utilization',
               'JOBNAME', f'RSPLEXL4:{hostname.upper()}:MVSSYS', WAIT_JOB)


# In this test the while loop will repeat 10 times until the situation opens
def test_situation_open():
    z = JESAdapter(hostname, username, password)
    job = z.submit_jcl(path_relative=True, path='resources/jobs/wait.jcl',
                       params={'{seconds}': '90', '{job}': WAIT_JOB}, wait=False)
    em = u.logon_beacon(hostname, applid, username, password)
    try:
        d = em.display
        open_situation = False
        cur_try = 0
        while not open_situation and cur_try < 10:
            time.sleep(10)
            if d.find('Open') is None:
                d.find('Navigate')('').enter()
                d('c').enter()
                d.find('Navigate')('').enter()
                d('e').enter()
                d.find('+  z/OS')('', key=keys.ENTER)
                if d.find(regex=f'\+(\s+)RSPLEXL4:{hostname.upper()}:MVSSYS'):
                    d.find(regex=f'\+(\s+)RSPLEXL4:{hostname.upper()}:MVSSYS')('', key=keys.ENTER)
                    sit_already_there = d.find(regex=f'\+(\s+){SIT_NAME}')
                    if sit_already_there:
                        # "click" to open to see the state
                        sit_already_there('', key=keys.ENTER)
            else:
                open_situation = True
            cur_try += 1
        assert d.find('Open')
    finally:
        u.close_beacon(em)


def test_monitoring_the_situation_state_in_tom_situations_status_tree(e3270_in_out):
    d = e3270_in_out
    cur_try = 0
    closed_situation = False
    while not closed_situation and cur_try < 5:
        time.sleep(60)
        cur_try += 1
        d.find('Navigate')('').enter()
        d('e').enter()
        d.find('+  z/OS')('').enter()
        d.find(regex=f'\+(\s+)RSPLEXL4:{hostname.upper()}:MVSSYS')('').enter()
        sit = d.find(regex=f'\+(\s+){SIT_NAME}')
        if sit:
            sit('').enter()
            if d.find('Closed'):
                closed_situation = True
        d('', key=keys.PF3)
    assert closed_situation


def test_panel_doesnt_crash_while_exiting_situation_editor(zosmf, e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1460
    Testing if panel doesn`t crash while getting back from situation editor and expanding z/OS tree again.
    """
    d = e3270_in_out
    d(key=keys.HOME)
    d.find('+  z/OS')('').enter()
    d.find(regex=f'\+(\s+)(\w+):MVS:SYSPLEX')('').enter()
    d.find(regex=f'\+(\s+){SIT_NAME}')('').enter()
    d('', key=keys.TAB)
    d('E').enter()
    d('', key=keys.PF3)
    d.find('+  z/OS')('').enter(timeout=10)
    assert not d.find('Command E is not a valid command')
    assert not d.find('OB0900')
    assert d.find(regex=f'(\w+):MVS:SYSPLEX')


def test_verify_situation_search(e3270_in_out):
    """
    Test to verify if situation search is working.
    """
    d = e3270_in_out
    d(key=keys.HOME)
    sit_name = 'IMS_Inactive'
    d('e.s', key=keys.ENTER)
    assert u.get_current_panel(d) == 'KOBSED1'
    d.find_by_label('Find:')(f'{sit_name}').enter()
    d.find('+    IMS')('').enter()
    assert d.find(f'IMS\n  {sit_name}\nJava Virtual Machines')


def test_delete_sit(e3270_in_out):
    d = e3270_in_out
    assert find_sit(e3270_in_out, SIT_NAME, 'MVS System'), 'SIT not found'
    u.zoom_in(SIT_NAME, 'd')
    assert d.find('Confirm Situation Delete')
    d('y', key=keys.ENTER)
    assert d.find('Success: Situation was deleted')
    d('', key=keys.ENTER)
    d('', key=keys.PF3)
    assert not find_sit(e3270_in_out, SIT_NAME, 'MVS System'), 'SIT is still found'


def test_sit_status(e3270_in_out):
    assert find_sit(e3270_in_out, 'DB2_Plex_Heartbeat', 'MVS DB2')
    assert e3270_in_out.find(regex='DB2_Plex_Heartbeat .* Started ')


def test_sit_status_when_hub_switched(e3270_in_out):
    assert switch_hub(e3270_in_out, rtes[rte]['hub_name'])
    assert find_sit(e3270_in_out, 'DB2_Plex_Heartbeat', 'MVS DB2')
    assert e3270_in_out.find(regex='DB2_Plex_Heartbeat .* Started ')
