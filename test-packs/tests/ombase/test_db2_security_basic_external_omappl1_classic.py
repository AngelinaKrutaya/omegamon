import pytest

from taf.zos.py3270 import Emulator
from taf.zos.py3270 import keys
from taf.af_support_tools import TAFConfig
from taf import logging
from libs.ivtenv import rtes
from libs import utils

from libs.ite1db2 import *


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
            welcome.shift((1, 0))(f"L {applid} DATA='LROWS=9999,DB2={ssid}'", keys.ENTER, 240)
        d(user, keys.NEWLINE)
        d(password, keys.ENTER)

        yield d
    finally:
        em.disconnect()
        em.close()



def setup_module(module):
    utils.set_security(hostname, username, password,  rtes[rte]['rte_hlq'], rte, omegamon, 'basic-omappl1',
                       ('KO2SUPD', 'KO2RACFA'), stc_job, 120)


#### TESTS


def test_classic_omappl1_authorized(classic_in_out):
    d = classic_in_out
    assert d.find('ZMENU    VTM')


@pytest.mark.parametrize('classic_in_out', [(username[:-1]+'b' if username.upper().endswith('A') else username+'b')],
                         indirect=True)
def test_classic_omappl1_non_authorized(classic_in_out):
    d = classic_in_out
    assert d.find('Security routine has aborted startup')




