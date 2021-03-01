import pytest

from taf.zos.py3270 import keys
from taf.af_support_tools import TAFConfig
from libs.ivtenv import rtes
from taf import logging

from libs import utils
from libs.db2utils import classic_in_out_func
from libs.ite1db2 import *


logger = logging.getLogger(__name__)
rte = os.environ.get('rte', 'ite1')

root = TAFConfig().testpack_root


@pytest.fixture(scope='function')
def classic_in_out(request):
    user = username
    if hasattr(request, 'param'):    
        user = request.param

    for x in classic_in_out_func(user, password, hostname, applid, ssid):
        yield x


def setup_module(module):
    utils.set_security(hostname, username, password,  rtes[rte]['rte_hlq'], rte, omegamon, 'passphrase-basic',
                       ('KO2SUPD', 'KO2RACFA'), stc_job, 120)


#### TESTS


def check_peek_panel(d, mess):
    assert d.find('ZMENU    VTM')
    d('m', key=keys.ENTER)
    assert d.find('ZDISP')
    d('b', key=keys.ENTER)
    assert d.find('ZPEEKBB')
    assert d.find('Security check failed (INTERNAL)')
    d('/pwd', key=keys.ENTER)
    d('ibm3', key=keys.ENTER)
    d(key=keys.ENTER)
    assert d.find(mess)


def test_classic_command_authorized_user1(classic_in_out):
    check_peek_panel(classic_in_out, 'Data Collection Initiated' )


@pytest.mark.parametrize('classic_in_out', [(username[:-1]+'b' if username.upper().endswith('A') else username+'b')],
                         indirect=True)
def test_classic_command_authorized_user2(classic_in_out):
    check_peek_panel(classic_in_out, 'Data Collection Initiated')

