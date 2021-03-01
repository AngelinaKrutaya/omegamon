import pytest

from taf.zos.py3270 import Emulator
from taf.zos.py3270 import keys
from taf.af_support_tools import TAFConfig

from taf import logging

from libs import utils
from libs.ivtenv import rtes
from libs.ite1cics import *

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
            welcome.shift((1, 0))(f"L {applid} DATA='cics={cics_job}'", keys.ENTER, 240)

        d.find('ENTER USERID')
        d(user, keys.NEWLINE)
        d(password, keys.ENTER)

        assert d.find('ZMENU    VTM')
        yield d
        d(key=keys.PF3)
        d('X', key=keys.ENTER)
    finally:
        em.disconnect()
        em.close()


def setup_module(module):
    utils.set_security(hostname, username, password, rtes[rte]['rte_hlq'], rte, omegamon, 'passphrase',
                       ('KOCSUPD', 'KOCRACFA'), stc_job)


#### TESTS


def check_task_panel(d, mess):
    d('t', key=keys.ENTER)
    assert d.find('ZTKALL')
    assert d.find(mess)
    d(key=keys.PF3)


def test_classic_task_authorized(classic_in_out):
    check_task_panel(classic_in_out, 'Tran          Task  Task')


@pytest.mark.parametrize('classic_in_out', [(username[:-1]+'b' if username.upper().endswith('A') else username+'b')],
                         indirect=True)
def test_classic_task_non_authorized(classic_in_out):
    check_task_panel(classic_in_out, 'Security System has determined that you are not authorized')