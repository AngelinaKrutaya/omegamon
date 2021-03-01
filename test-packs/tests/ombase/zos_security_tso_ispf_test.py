import os
import pytest

from taf.zos.py3270 import ISPF
from taf.zos.py3270 import Emulator
from taf.zos.py3270 import keys
from taf.zos.zosmflib import zOSMFConnector

from libs.ivtenv import rtes
from libs.creds import *

from libs import utils

username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)


@pytest.fixture(scope='module', params=rte_names)
def rte_setup(request):
    rte = request.param
    omegamon = 'zos'
    hostname = rtes[rte]['hostname']
    # for these tests, we don't need stc, but we need to start it just to make sure libs are APF authorized
    utils.set_security(hostname, username, password, rtes[rte]['rte_hlq'], rte, omegamon, 'basic',
                       ('KOMSUPD', 'KOMRACFA'), f'{rte}M2RC')
    # prepare ispf logon
    # we need to copy KOMSPF and KOMSPFU,
    # KOMSPFSC, KOMSPFSI, KOMSPFSX for new ispf logon from *.RKANSAMU to to ROCKET.USER.CLIST
    z = zOSMFConnector(hostname, username, password)
    for mem in ('KOMSPF', 'KOMSPFU', 'KOMSPFSC', 'KOMSPFSI', 'KOMSPFSX'):
        read_mem = z.read_ds(f"{rtes[rte]['rte_hlq']}.RKANSAMU({mem})")
        z.write_ds(f'ITM.ITE.QA.CLIST({mem})', read_mem)
    return rte


@pytest.fixture(scope='function')
def tso_in_out(request, rte_setup):
    rte = rte_setup
    user = username
    if hasattr(request, 'param'):
        user = request.param

    em = Emulator(rtes[rte]['hostname'], model=2, oversize=(24, 80))
    ispf = ISPF(em, username=user, password=password)
    d = ispf.em.display
    d(key=keys.PF3)
    d(text=f"ex '{rtes[rte]['rte_hlq']}.RKANSAMU(KOMCLSTE)'", key=keys.ENTER)
    assert d.find('Please press ENTER to begin')
    d(key=keys.ENTER)
    assert d.find('ZMENU    TSO     OM/DEX')
    yield d
    d(key=keys.PF3)
    d('X', key=keys.ENTER)
    d('ispf', key=keys.ENTER)
    ispf.logoff()


# TESTS

def check_kill_panel(d, mess):
    d('a', key=keys.ENTER)
    assert d.find('ZACTN')
    d('g', key=keys.ENTER)
    assert d.find('ZKILL')
    assert d.find(mess)
    d(key=keys.PF3)
    d(key=keys.PF3)


def test_tso_logon(tso_in_out):
    d = tso_in_out
    assert d.find('ZMENU    TSO     OM/DEX')


def test_tso_kill_authorized(tso_in_out):
    check_kill_panel(tso_in_out, 'Enter decimal ASID or Jobname')


@pytest.mark.parametrize('tso_in_out', [(username[:-1] + 'b' if username.upper().endswith('A') else username + 'b')],
                         indirect=True)
def test_tso_kill_non_authorized(tso_in_out):
    check_kill_panel(tso_in_out, 'RACF HAS DETERMINED THAT YOU ARE NOT AUTHORIZED')


def test_tso_dataset_security(tso_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-936
    This is to test that TSO mode still works fine
    :param tso_in_out:
    :return:
    """
    d = tso_in_out
    assert d.find('ZMENU    TSO     OM/DEX')
    d('j.a').enter()
    assert d.find('Number of Users Logged On')
    d(key=keys.PF11)
    assert d.find('Examine Details for Job')
    d('j').enter()
    assert d.find('Security check failed (INTERNAL)')
    d('/pwd').enter()
    d('omegam3').enter()
    assert d.find('Password accepted')
    d('').enter()
    assert d.find('Addr VolSer Sta,Dsp')
    d(key=keys.PF3)
    d(key=keys.PF3)
    d(key=keys.PF3)
    d(key=keys.PF3)


# ISPF

def test_ispf_logon_with_komspf_is_disabled(rte_setup):
    """
    After https://jira.rocketsoftware.com/browse/OMBS-936
    full ISPF is disabled
    :return:
    """
    rte = rte_setup
    em = Emulator(rtes[rte]['hostname'], model=2, oversize=(24, 80))
    ispf = ISPF(em, username=username, password=password)
    d = ispf.em.display
    d('6', key=keys.ENTER)
    d(text="ALTLIB ACTIVATE APPL(CLIST) DA('ITM.ITE.QA.CLIST')", key=keys.ENTER)
    d('komspf', key=keys.ENTER)
    d('3', key=keys.ENTER)
    if d.find('KOMSPF - KEY ASSIGNMENT PANEL'):
        d(key=keys.ENTER)
    assert d.find('OB1230 Full ISPF mode is not supported')
    d(key=keys.ENTER)
    d('x', key=keys.ENTER)
    ispf.logoff()


def test_ispf_logon(rte_setup):
    """
    After https://jira.rocketsoftware.com/browse/OMBS-936
    we get TSO mode, actually
    :return:
    """
    rte = rte_setup
    em = Emulator(rtes[rte]['hostname'], model=2, oversize=(24, 80))
    ispf = ISPF(em, username=username, password=password)
    d = ispf.em.display
    d(key=keys.PF3)
    assert d.find('READY')
    d(text="ALTLIB ACTIVATE APPL(CLIST) DA('ITM.ITE.QA.CLIST')", key=keys.ENTER)
    d('KOMSPFSI', key=keys.ENTER)
    assert d.find('KOMSPFSI\n READY')
    d('ispf', key=keys.ENTER)
    assert d.find('ISPF Primary Option Menu')
    d('6', key=keys.ENTER)
    d(text="ALTLIB ACTIVATE APPL(CLIST) DA('ITM.ITE.QA.CLIST')", key=keys.ENTER)
    d('TSO KOMSPFSX', key=keys.ENTER)
    assert d.find('Please press ENTER to begin')
    d(key=keys.ENTER)
    assert d.find('ZMENU    TSO     OM/DEX')
    d(key=keys.PF3)
    d('X', key=keys.ENTER)
    ispf.logoff()
