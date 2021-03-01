import pytest

from taf.zos.py3270 import Emulator
from taf.zos.py3270 import keys
from taf.af_support_tools import TAFConfig
from libs.ivtenv import rtes
from taf import logging

from libs import utils
from libs.ite1ims import *

logger = logging.getLogger(__name__)
rte = os.environ.get('rte', 'ite1')

root = TAFConfig().testpack_root


@pytest.fixture(scope='function')
def classic_in_out(request):
    user = username
    if hasattr(request, 'param'):    
        user = request.param

    em = Emulator(hostname, model=2, oversize=(24, 80))
    d = em.display
    try:
        welcome = d.find('===> Ex.: LOGON <userid>, TSO <userid>')
        if welcome:
            logger.info(f"Logging to Classic applid {applid}")
            welcome.shift((1, 0))(f"L {applid}", keys.ENTER, 240)
            # welcome.shift((1, 0))(f"L {applid} DATA='cics={cics_job},LROWS=9999'", keys.ENTER, 30)
        #welcome(key=Keys.ENTER, wait_for="Please press ENTER to begin")

        d.find('ENTER USERID')
        d(user, keys.NEWLINE)
        d(password, keys.ENTER)

        assert d.find('ZMENU    VTM     OI-II')
        yield d
        d(key=keys.PF3)
        d('X', key=keys.ENTER)
    finally:
        em.disconnect()
        em.close()



def setup_module(module):
    utils.set_security(hostname, username, password,  rtes[rte]['rte_hlq'], rte, omegamon, 'passphrase',
                       ('KOISUPD', 'KOIRACFA'), stc_job)


#### TESTS


def check_icmd_panel(d, mess):
    d('t', key=keys.ENTER)
    assert d.find('KOITOOL')
    d('a', key=keys.ENTER)
    assert d.find('KOICONS')
    command = d.find('>OCMD               ')
    command('-ICMD /DIS DB ALL', key=keys.ENTER)
    assert d.find(mess)
    d(key=keys.PF3)
    d(key=keys.PF3)


def test_classic_icmd_authorized(classic_in_out):
    check_icmd_panel(classic_in_out, 'RC =  0')


@pytest.mark.parametrize('classic_in_out', [(username[:-1]+'b' if username.upper().endswith('A') else username+'b')],
                         indirect=True)
def test_classic_icmd_non_authorized(classic_in_out):
    check_icmd_panel(classic_in_out, 'Security System has determined that you are not authorized')


