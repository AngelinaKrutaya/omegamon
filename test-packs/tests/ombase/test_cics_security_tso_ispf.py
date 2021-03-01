import pytest

from taf.zos.py3270 import ISPF
from taf.zos.py3270 import Emulator
from taf.zos.py3270 import keys
from taf.af_support_tools import TAFConfig
from libs.ivtenv import rtes
from taf import logging

from libs import utils
from libs.ite1cics import *


logger = logging.getLogger(__name__)
rte = os.environ.get('rte', 'ite1')

root = TAFConfig().testpack_root


@pytest.fixture(scope='function')
def tso_in_out(request):
    user = username
    if hasattr(request, 'param'):    
        user = request.param

    em = Emulator(hostname, model=2, oversize=(24, 80))
    ispf = ISPF(em, username=user, password=password)
    d = ispf.em.display
    try:
        d(key=keys.PF3)
        d(text=f"ALTLIB ACTIVATE APPL(CLIST) DA('{rtes[rte]['clist']}')", key=keys.ENTER)
        d(text='%KOCLIST', key=keys.ENTER)

        d(user, keys.NEWLINE)
        d(password, keys.ENTER)

        assert d.find('ZMENU    VTT')
        yield d
        d(key=keys.PF3)
        d('X', key=keys.ENTER)
        d('ispf', key=keys.ENTER)
    finally:
        ispf.logoff()


@pytest.fixture(scope='function')
def ispf_in_out(request):
    user = username
    if hasattr(request, 'param'):    
        user = request.param

    em = Emulator(hostname, model=2, oversize=(24, 80))
    ispf = ISPF(em, username=user, password=password)
    d = ispf.em.display
    d('6', key=keys.ENTER)
    d(text=f"ALTLIB ACTIVATE APPL(CLIST) DA('{rtes[rte]['clist']}')", key=keys.ENTER)
    d('%KOCLIST', key=keys.ENTER)
    assert d.find('OCALIST - INVOCATION MENU')

    appl = d.find_by_label('OBVTAM APPL ===>')
    appl(text=applid, key=keys.NEWLINE)
    d(cics_job)
    option = d.find_by_label('OPTION  ===>')
    option('2', key=keys.ENTER)

    d(user, keys.NEWLINE)
    d(password, keys.ENTER)

    assert d.find('ZMENU    VTS')
    yield d
    d(key=keys.PF3)
    d('X', key=keys.ENTER)
    d('X', key=keys.ENTER)
    ispf.logoff()


def setup_module(module):
    utils.set_security(hostname, username, password,  rtes[rte]['rte_hlq'], rte, omegamon, 'basic',
                       ('KOCSUPD', 'KOCRACFA'), stc_job)

#### TESTS


def check_task_panel(d, mess):
    d('t', key=keys.ENTER)
    assert d.find('ZTKALL')
    assert d.find(mess)
    d(key=keys.PF3)


def test_tso_logon(tso_in_out):
    d = tso_in_out
    assert d.find('ZMENU    VTT')


def test_tso_task_authorized(tso_in_out):
    check_task_panel(tso_in_out, 'Tran          Task  Task')


@pytest.mark.parametrize('tso_in_out', [(username[:-1]+'b' if username.upper().endswith('A') else username+'b')],
                         indirect=True)
def test_tso_task_non_authorized(tso_in_out):
    check_task_panel(tso_in_out, 'RACF HAS DETERMINED THAT YOU ARE NOT AUTHORIZED')


######## ISPF


def test_ispf_logon(ispf_in_out):
    d = ispf_in_out
    assert d.find('O M E G A M O N   I S P F   I N T E R F A C E')
    assert d.find('ZMENU    VTS')


def test_ispf_task_authorized(ispf_in_out):
    check_task_panel(ispf_in_out, 'Tran          Task  Task')


@pytest.mark.parametrize('ispf_in_out', [(username[:-1]+'b' if username.upper().endswith('A') else username+'b')],
                         indirect=True)
def test_ispf_task_non_authorized(ispf_in_out):
    check_task_panel(ispf_in_out, 'RACF HAS DETERMINED THAT YOU ARE NOT AUTHORIZED')

