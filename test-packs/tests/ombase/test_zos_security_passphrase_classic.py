import pytest

from taf.zos.py3270 import Emulator
from taf.zos.py3270 import keys
from taf.af_support_tools import TAFConfig
from libs.ivtenv import rtes
from taf import logging

from libs import utils
from libs.ite1zos import *


logger = logging.getLogger(__name__)
rte = os.environ.get('rte', 'ite1')

root = TAFConfig().testpack_root


@pytest.fixture(scope='function')
def classic_in_out(request):
    user = username
    if hasattr(request, 'param'):    
        user = request.param

    em = Emulator(hostname, model=2, oversize=(24, 80))
    try:
        d = em.display

        welcome = d.find('===> Ex.: LOGON <userid>, TSO <userid>')
        if welcome:
            logger.info(f"Logging to Classic applid {applid}")
            welcome.shift((1, 0))(f"L {applid} DATA='LROWS=9999'", keys.ENTER, 240)

        d(user, keys.NEWLINE)
        d(password, keys.ENTER)

        assert d.find('ZMENU    VTM     OM/DEX')
        yield d
        d(key=keys.PF3)
        d('X', key=keys.ENTER)
    finally:
        em.disconnect()
        em.close()


def setup_module(module):
    utils.set_security(hostname, username, password,  rtes[rte]['rte_hlq'], rte, omegamon, 'passphrase',
                       ('KOMSUPD', 'KOMRACFA'), stc_job)


#### TESTS


def check_kill_panel(d, mess):
    d('a', key=keys.ENTER)
    assert d.find('ZACTN')
    d('g', key=keys.ENTER)
    assert d.find('ZKILL')
    assert d.find(mess)
    d(key=keys.PF3)
    d(key=keys.PF3)


def test_classic_kill_authorized(classic_in_out):
    check_kill_panel(classic_in_out, 'Enter decimal ASID or Jobname')


@pytest.mark.parametrize('classic_in_out', [(username[:-1]+'b' if username.upper().endswith('A') else username+'b')],
                         indirect=True)
def test_classic_kill_non_authorized(classic_in_out):
    check_kill_panel(classic_in_out, 'Security System has determined that you are not authorized')

